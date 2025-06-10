import logging
import datetime as dt
import json
from dateutil.parser import parse as parse_date
from dateutil.relativedelta import relativedelta
from fhirclient import client
from fhirclient.models import patient, observation, condition, medicationrequest, procedure

# --- Load CDSS Config ---
try:
    with open('cdss_config.json', 'r', encoding='utf-8') as f:
        CDSS_CONFIG = json.load(f)
    logging.info("Successfully loaded cdss_config.json")
except FileNotFoundError:
    logging.error("CRITICAL: cdss_config.json not found. Calculations will fail.")
    CDSS_CONFIG = {}
except json.JSONDecodeError:
    logging.error("CRITICAL: cdss_config.json is not valid JSON. Calculations will fail.")
    CDSS_CONFIG = {}

# --- Configuration for LOINC codes (5-item PRECISE-DAPT) ---
LOINC_CODES = {
    "EGFR": ("33914-3",),          # Glomerular filtration rate/1.73 sq M predicted
    "CREATININE": ("2160-0",),      # Creatinine [mass/volume] in Serum or Plasma
    "HEMOGLOBIN": ("718-7",),       # Hemoglobin [Mass/volume] in Blood
    "WBC": ("26464-8", "6690-2", "33256-9"),  # White blood cells [#/volume] in Blood (multiple LOINC codes)
}

def get_fhir_data(fhir_server_url, access_token, patient_id, client_id):
    """
    Fetches all required patient data using the fhirclient library.
    This provides better compatibility with various FHIR servers including Cerner.
    
    Returns a dictionary of FHIR resources and an error message if any.
    """
    try:
        # Set up FHIR client settings following smart-on-fhir/client-py best practices
        settings = {
            'app_id': client_id,
            'api_base': fhir_server_url,
            'patient_id': patient_id,
        }
        
        # Create FHIR client instance
        smart = client.FHIRClient(settings=settings)
        
        # Set authorization using the standard fhirclient approach
        if access_token:
            # Method 1: Use the built-in authorize method (most compatible)
            smart.prepare()
            
            # Method 2: Set the authorization directly on the server
            if hasattr(smart.server, 'prepare'):
                smart.server.prepare()
            
            # Method 3: Set authorization header properly for fhirclient
            smart.server.auth = None  # Clear any existing auth
            
            # Set proper headers for FHIR requests
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/fhir+json, application/json',
                'Content-Type': 'application/fhir+json'
            }
            
            # Use the server's session to set headers
            if hasattr(smart.server, 'session'):
                smart.server.session.headers.update(headers)
            else:
                # Create session if it doesn't exist
                import requests
                smart.server.session = requests.Session()
                smart.server.session.headers.update(headers)
            
            # Also set the _auth for backward compatibility
            smart.server._auth = None  # Clear old auth
            
            logging.info(f"Set authorization header with token length: {len(access_token)}")
            logging.info(f"FHIR Server prepared for: {fhir_server_url}")
        
        # Test the connection with a simple patient fetch first
        try:
            logging.info(f"Attempting to fetch patient {patient_id} from {fhir_server_url}")
            
            # Use the standard fhirclient Patient.read method
            patient_resource = patient.Patient.read(patient_id, smart.server)
            logging.info(f"Successfully fetched Patient resource for patient: {patient_id}")
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Detailed error fetching patient: {error_msg}")
            
            # Log additional debugging information
            if hasattr(smart.server, 'session') and hasattr(smart.server.session, 'headers'):
                headers_dict = dict(smart.server.session.headers)
                # Don't log the full token for security
                if 'Authorization' in headers_dict:
                    headers_dict['Authorization'] = 'Bearer ***REDACTED***'
                logging.info(f"Request headers: {headers_dict}")
            
            # Log the exact URL being called
            if hasattr(smart.server, 'base_uri'):
                logging.info(f"Base URI: {smart.server.base_uri}")
            
            if '401' in error_msg:
                logging.error(f"Authentication failed - Access token may be expired or invalid")
                # Try to provide more specific error information
                if 'expired' in error_msg.lower():
                    return None, f"Access token has expired. Please re-launch the application from your EHR."
                elif 'invalid' in error_msg.lower():
                    return None, f"Access token is invalid. Please re-launch the application from your EHR."
                else:
                    return None, f"Authentication failed. Please re-launch the application from your EHR. Details: {str(e)}"
            elif '403' in error_msg:
                logging.error(f"Permission denied - Insufficient scope or patient access")
                return None, f"Access denied. The application may not have permission to access this patient's data. Please check the application's scope configuration."
            elif '404' in error_msg:
                logging.error(f"Patient not found")
                return None, f"Patient {patient_id} not found in the FHIR server."
            else:
                logging.error(f"Failed to fetch patient resource")
                return None, f"Failed to retrieve patient data: {str(e)}"

        raw_data = {"patient": patient_resource.as_json()}
        
        # Fetch observations by LOINC codes (updated for PRECISE-DAPT parameters)
        for resource_type, codes in LOINC_CODES.items():
            try:
                # Search for observations with specific LOINC codes
                # Using more compatible query parameters
                search_params = {
                    'patient': patient_id,
                    'code': ','.join(codes),
                    '_count': '5'  # Get a few results to find the most recent
                }
                
                observations = observation.Observation.where(search_params).perform(smart.server)
                obs_list = []
                
                if observations.entry:
                    # Sort by effective date in memory (more compatible than _sort parameter)
                    sorted_entries = []
                    for entry in observations.entry:
                        if entry.resource:
                            resource_json = entry.resource.as_json()
                            # Extract date for sorting
                            date_str = resource_json.get('effectiveDateTime') or resource_json.get('effectivePeriod', {}).get('start') or '1900-01-01'
                            sorted_entries.append((date_str, resource_json))
                    
                    # Sort by date (most recent first) and take the first one
                    sorted_entries.sort(key=lambda x: x[0], reverse=True)
                    if sorted_entries:
                        obs_list.append(sorted_entries[0][1])  # Take the most recent
                
                raw_data[resource_type] = obs_list
                logging.info(f"Successfully fetched {len(obs_list)} {resource_type} observation(s)")
                
            except Exception as e:
                logging.warning(f"Error fetching {resource_type} observations (continuing with empty list): {e}")
                raw_data[resource_type] = []
        
        # Fetch conditions (for bleeding history)
        try:
            # Use larger count to get more comprehensive condition data
            # Try with fallback strategy for better compatibility and timeout handling
            conditions_list = []
            
            try:
                logging.info(f"Attempting to fetch conditions with _count=100 for patient {patient_id}")
                conditions_search = condition.Condition.where({
                    'patient': patient_id,
                    '_count': '100'  # Try 100 first
                }).perform(smart.server)
                
                if conditions_search.entry:
                    for entry in conditions_search.entry:  # Process all returned conditions
                        if entry.resource:
                            conditions_list.append(entry.resource.as_json())
                
                logging.info(f"Successfully fetched {len(conditions_list)} condition(s) with _count=100")
                
            except Exception as e:
                error_str = str(e)
                if '504' in error_str or 'timeout' in error_str.lower() or 'gateway time-out' in error_str.lower():
                    logging.warning(f"Timeout with _count=100, trying smaller count: {e}")
                    # Fallback to smaller count on timeout
                    try:
                        conditions_search = condition.Condition.where({
                            'patient': patient_id,
                            '_count': '20'
                        }).perform(smart.server)
                        
                        if conditions_search.entry:
                            for entry in conditions_search.entry:
                                if entry.resource:
                                    conditions_list.append(entry.resource.as_json())
                        
                        logging.info(f"Successfully fetched {len(conditions_list)} condition(s) with _count=20 fallback")
                        
                    except Exception as e2:
                        logging.warning(f"Fallback with _count=20 also failed, trying minimal count: {e2}")
                        # Final fallback to very small count
                        try:
                            conditions_search = condition.Condition.where({
                                'patient': patient_id,
                                '_count': '5'
                            }).perform(smart.server)
                            
                            if conditions_search.entry:
                                for entry in conditions_search.entry:
                                    if entry.resource:
                                        conditions_list.append(entry.resource.as_json())
                            
                            logging.info(f"Successfully fetched {len(conditions_list)} condition(s) with _count=5 minimal fallback")
                            
                        except Exception as e3:
                            logging.error(f"All condition fetching strategies failed: {e3}")
                            conditions_list = []
                            
                elif '401' in error_str or '403' in error_str:
                    logging.warning(f"Permission issue with _count=100, trying smaller count: {e}")
                    # Permission-based fallback (existing logic)
                    conditions_search = condition.Condition.where({
                        'patient': patient_id,
                        '_count': '20'
                    }).perform(smart.server)
                    
                    if conditions_search.entry:
                        for entry in conditions_search.entry:
                            if entry.resource:
                                conditions_list.append(entry.resource.as_json())
                    
                    logging.info(f"Successfully fetched {len(conditions_list)} condition(s) with _count=20 permission fallback")
                else:
                    raise e
            
            raw_data['conditions'] = conditions_list
            logging.info(f"Final result: {len(conditions_list)} condition(s) stored")
            
        except Exception as e:
            logging.warning(f"Error fetching conditions (continuing with empty list): {e}")
            raw_data['conditions'] = []
        
        # For PRECISE-DAPT, we don't need medications and procedures, but keep minimal fetch for compatibility
        raw_data['med_requests'] = []
        raw_data['procedures'] = []

        return raw_data, None

    except Exception as e:
        logging.error(f"An unexpected error occurred in get_fhir_data: {e}", exc_info=True)
        return None, str(e)

# --- Data Processing and Risk Calculation Logic for PRECISE-DAPT ---

def _resource_has_code(resource, system, code):
    """Checks if a resource's coding matches the given system and code."""
    for coding in resource.get('code', {}).get('coding', []):
        if coding.get('system') == system and coding.get('code') == code:
            return True
    return False

def _is_within_time_window(resource_date_str, min_months=None, max_months=None):
    """Checks if a resource date is within the specified time window from today."""
    if not resource_date_str:
        return False
    try:
        resource_date = parse_date(resource_date_str).date()
        today = dt.date.today()
        if min_months is not None and resource_date > today - relativedelta(months=min_months):
            return False
        if max_months is not None and resource_date < today - relativedelta(months=max_months):
            return False
        return True
    except (ValueError, TypeError):
        return False

def get_patient_demographics(patient_resource):
    """Extracts and formats patient's name, age, and gender."""
    if not patient_resource:
        return {'name': "Unknown", 'age': None, 'gender': "unknown"}

    # Name
    name_data = patient_resource.get('name', [{}])[0]
    given_name = " ".join(name_data.get('given', []))
    family_name = name_data.get('family', "")
    name = f"{given_name} {family_name}".strip()

    # Age
    birth_date_str = patient_resource.get('birthDate')
    age = None
    if birth_date_str:
        try:
            birth_date = dt.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            today = dt.date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except (ValueError, TypeError):
            logging.warning(f"Could not parse birthDate: {birth_date_str}")

    return {
        'name': name or "Unknown",
        'age': age,
        'gender': patient_resource.get('gender', 'unknown')
    }

def get_value_from_observation(obs, to_g_dl=False):
    """Extracts value, unit, and date from an observation resource."""
    if not obs or 'valueQuantity' not in obs:
        return None, None, None
    
    value = obs['valueQuantity'].get('value')
    # Round the value if it's a number
    if isinstance(value, (int, float)):
        value = round(value, 2)

    unit = obs['valueQuantity'].get('unit')
    date = obs.get('effectiveDateTime', 'Unknown Date')[:10]
    
    if to_g_dl and unit and value and unit.lower() == 'g/l':
        value /= 10
        unit = 'g/dL' # Update unit after conversion
        
    return value, unit, date

def calculate_egfr(cr_val, age, gender):
    """Calculates eGFR using the CKD-EPI 2021 equation."""
    if not all([cr_val, age, gender]) or gender not in ['male', 'female']:
        return None, "Missing data for eGFR calculation"
    
    k = 0.7 if gender == 'female' else 0.9
    alpha = -0.241 if gender == 'female' else -0.302
    
    # CKD-EPI 2021 formula
    egfr = 142 * (min(cr_val / k, 1) ** alpha) * (max(cr_val / k, 1) ** -1.2) * (0.9938 ** age)
    if gender == 'female':
        egfr *= 1.012
        
    return round(egfr), "CKD-EPI 2021"

def get_score_from_table(value, score_table, range_key):
    """Helper function to get score from lookup tables."""
    for item in score_table:
        if range_key in item:
            range_values = item[range_key]
            if len(range_values) == 2 and range_values[0] <= value <= range_values[1]:
                return item.get('base_score', 0)
    return 0

def check_bleeding_history(conditions):
    """Checks for history of spontaneous bleeding in patient conditions."""
    if not CDSS_CONFIG:
        return False, []
    
    bleeding_codings = CDSS_CONFIG.get('bleeding_history_codings', {})
    bleeding_keywords = CDSS_CONFIG.get('bleeding_history_keywords', [])
    
    bleeding_evidence = []
    
    # Check SNOMED codes
    for condition in conditions:
        # Check coded conditions
        for coding in condition.get('code', {}).get('coding', []):
            system = coding.get('system', '')
            code = coding.get('code', '')
            
            # Check against bleeding history SNOMED codes
            for bleeding_type, code_list in bleeding_codings.items():
                for snomed_system, snomed_code in code_list:
                    if system == snomed_system and code == snomed_code:
                        display = coding.get('display', condition.get('code', {}).get('text', 'Bleeding history'))
                        bleeding_evidence.append(display)
                        break
        
        # Check text-based conditions
        condition_text = ""
        if condition.get('code', {}).get('text'):
            condition_text += condition['code']['text'].lower().strip() + " "
        for coding in condition.get('code', {}).get('coding', []):
            if coding.get('display'):
                condition_text += coding['display'].lower().strip() + " "
        
        condition_text = condition_text.strip()
        if condition_text:
            for keyword in bleeding_keywords:
                if keyword.lower() in condition_text:
                    display_text = condition.get('code', {}).get('text', 
                                                condition.get('code', {}).get('coding', [{}])[0].get('display', 'Bleeding history'))
                    bleeding_evidence.append(display_text)
                    break
    
    has_bleeding_history = len(bleeding_evidence) > 0
    return has_bleeding_history, bleeding_evidence

def calculate_precise_dapt_score(raw_data, demographics):
    """
    Calculates PRECISE-DAPT bleeding risk score based on 5-item model:
    1. Age
    2. Hemoglobin
    3. Creatinine clearance 
    4. White blood cell count
    5. Previous spontaneous bleeding
    
    Returns components list and total score.
    """
    if not CDSS_CONFIG:
        return [], 0
    
    components = []
    total_score = 0
    
    # Get scoring tables from config
    scoring_config = CDSS_CONFIG.get('scoring_nomogram', {})
    age_table = scoring_config.get('age_score_table', [])
    hb_table = scoring_config.get('hemoglobin_score_table', [])
    ccr_table = scoring_config.get('creatinine_clearance_score_table', [])
    wbc_table = scoring_config.get('wbc_score_table', [])
    bleeding_config = CDSS_CONFIG.get('precise_dapt_parameters', {}).get('previous_bleeding', {})
    
    # 1. Age Score
    age = demographics.get('age')
    if age:
        age_score = get_score_from_table(age, age_table, 'age_range')
        total_score += age_score
        components.append({
            "parameter": "PreciseDAPT - Age",
            "value": f"{age} years",
            "score": age_score,
            "date": "N/A",
            "description": f"Age contribution to PRECISE-DAPT score"
        })
    else:
        components.append({
            "parameter": "PreciseDAPT - Age", 
            "value": "Unknown",
            "score": 0,
            "date": "N/A",
            "description": "Age not available"
        })
    
    # 2. Hemoglobin Score
    hemoglobin_list = raw_data.get('HEMOGLOBIN', [])
    hemoglobin_obs = hemoglobin_list[0] if hemoglobin_list else {}
    hb_val, hb_unit, hb_date = get_value_from_observation(hemoglobin_obs, to_g_dl=True)
    
    if hb_val:
        hb_score = get_score_from_table(hb_val, hb_table, 'hb_range')
        total_score += hb_score
        components.append({
            "parameter": "PreciseDAPT - Hemoglobin",
            "value": f"{hb_val} {hb_unit}",
            "score": hb_score,
            "date": hb_date,
            "description": f"Hemoglobin contribution to PRECISE-DAPT score"
        })
    else:
        components.append({
            "parameter": "PreciseDAPT - Hemoglobin",
            "value": "Not available",
            "score": 0,
            "date": "N/A", 
            "description": "Hemoglobin not available"
        })
    
    # 3. Creatinine Clearance Score
    egfr_list = raw_data.get('EGFR', [])
    egfr_obs = egfr_list[0] if egfr_list else {}
    creatinine_list = raw_data.get('CREATININE', [])
    creatinine_obs = creatinine_list[0] if creatinine_list else {}
    
    egfr_val, _, egfr_date = get_value_from_observation(egfr_obs)
    
    ccr_final = None
    ccr_source = ""
    ccr_final_date = "N/A"
    
    if egfr_val:
        ccr_final = egfr_val
        ccr_source = "Direct eGFR"
        ccr_final_date = egfr_date
        logging.info(f"Using direct eGFR value: {ccr_final}")
    else:
        creatinine_val, _, cr_date = get_value_from_observation(creatinine_obs)
        if creatinine_val and age and demographics.get('gender'):
            logging.info("Direct eGFR not found, calculating from Creatinine.")
            calculated_egfr, reason = calculate_egfr(creatinine_val, age, demographics.get('gender'))
            if calculated_egfr:
                ccr_final = calculated_egfr
                ccr_source = reason
                ccr_final_date = cr_date
    
    if ccr_final:
        ccr_score = get_score_from_table(ccr_final, ccr_table, 'ccr_range')
        total_score += ccr_score
        components.append({
            "parameter": "PreciseDAPT - Creatinine Clearance",
            "value": f"{ccr_final} mL/min/1.73m² ({ccr_source})",
            "score": ccr_score,
            "date": ccr_final_date,
            "description": f"Kidney function contribution to PRECISE-DAPT score"
        })
    else:
        components.append({
            "parameter": "PreciseDAPT - Creatinine Clearance",
            "value": "Not available",
            "score": 0,
            "date": "N/A",
            "description": "Creatinine clearance not available"
        })
    
    # 4. White Blood Cell Count Score
    wbc_list = raw_data.get('WBC', [])
    wbc_obs = wbc_list[0] if wbc_list else {}
    wbc_val, wbc_unit, wbc_date = get_value_from_observation(wbc_obs)
    
    if wbc_val:
        wbc_score = get_score_from_table(wbc_val, wbc_table, 'wbc_range')
        total_score += wbc_score
        components.append({
            "parameter": "PreciseDAPT - White Blood Cell Count",
            "value": f"{wbc_val} {wbc_unit}",
            "score": wbc_score,
            "date": wbc_date,
            "description": f"White blood cell count contribution to PRECISE-DAPT score"
        })
    else:
        components.append({
            "parameter": "PreciseDAPT - White Blood Cell Count",
            "value": "Not available",
            "score": 0,
            "date": "N/A",
            "description": "White blood cell count not available"
        })
    
    # 5. Previous Bleeding History
    conditions = raw_data.get('conditions', [])
    has_bleeding, bleeding_evidence = check_bleeding_history(conditions)
    
    bleeding_score = 0
    if has_bleeding:
        bleeding_score = bleeding_config.get('score_values', {}).get('yes', 10)
        bleeding_display = bleeding_evidence[0] + (f" (+{len(bleeding_evidence)-1} more)" if len(bleeding_evidence) > 1 else "")
        total_score += bleeding_score
        components.append({
            "parameter": "PreciseDAPT - Prior Bleeding",
            "value": bleeding_display,
            "score": bleeding_score,
            "date": "Historical",
            "description": f"History of spontaneous bleeding"
        })
    else:
        components.append({
            "parameter": "PreciseDAPT - Prior Bleeding",
            "value": "No bleeding history found",
            "score": 0,
            "date": "N/A",
            "description": "No previous bleeding history"
        })
    
    return components, total_score

def calculate_risk_components(raw_data, demographics):
    """
    Main function to calculate PRECISE-DAPT bleeding risk score.
    Returns list of components and total score.
    """
    return calculate_precise_dapt_score(raw_data, demographics) 