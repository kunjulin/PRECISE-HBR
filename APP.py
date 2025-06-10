import os
import json
import logging
import uuid
import requests
from urllib.parse import urljoin, urlencode
from dotenv import load_dotenv

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, session, jsonify, url_for)
from flask_session import Session

from fhir_data_service import get_fhir_data, calculate_risk_components, get_patient_demographics, CDSS_CONFIG

# --- App Initialization & Configuration ---

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# In a real app, this should be a more robust secret management strategy
app.secret_key = os.environ.get('FLASK_SECRET_KEY', str(uuid.uuid4()))

# Configure server-side sessions for App Engine
# The /tmp directory is the only writable directory in App Engine's standard environment.
SESSION_DIR = "/tmp/flask_session"
# Ensure the session directory exists
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_DIR
Session(app)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# These must match your Cerner developer portal registration
CLIENT_ID = os.environ.get('SMART_CLIENT_ID', 'your-client-id-here')
# The redirect_uri must be the full URL to the /callback endpoint
# It's crucial that this matches the registration EXACTLY.
REDIRECT_URI = os.environ.get('SMART_REDIRECT_URI', 'http://localhost:5000/callback')
# The scopes required by the application
SCOPES = "launch patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/Procedure.read fhirUser openid profile online_access"

# --- Cerner Sandbox Configuration ---
# Default Cerner sandbox endpoints for testing
CERNER_SANDBOX_CONFIG = {
    'fhir_base': 'https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d',
    'authorization_endpoint': 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/personas/provider/authorize',
    'token_endpoint': 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v1/token',
    'tenant_id': 'ec2458f2-1e24-41c8-b71b-0e701af7583d'
}

# --- Pre-flight Checks for Essential Configuration ---
if not CLIENT_ID or not REDIRECT_URI:
    logging.critical("FATAL: SMART_CLIENT_ID and SMART_REDIRECT_URI must be set in the environment.")
    # This is a simple way to halt execution if config is missing.
    # In a more complex app, you might raise a custom exception.
    raise SystemExit("Error: Application is not configured. Please set SMART_CLIENT_ID and SMART_REDIRECT_URI.")

# --- Utility Functions ---

def get_smart_config(fhir_server_url):
    """
    Fetches the SMART configuration. First tries the .well-known/smart-configuration endpoint,
    then falls back to parsing the CapabilityStatement from the /metadata endpoint.
    """
    # Ensure the base URL ends with a slash for correct relative path joining.
    if not fhir_server_url.endswith('/'):
        fhir_server_url += '/'

    # 1. Try .well-known/smart-configuration first
    try:
        url = urljoin(fhir_server_url, ".well-known/smart-configuration")
        logging.info(f"Attempting to fetch SMART config from: {url}")
        response = requests.get(url, headers={'Accept': 'application/json'})
        response.raise_for_status()
        config = response.json()
        if 'authorization_endpoint' in config and 'token_endpoint' in config:
            logging.info("Successfully fetched SMART configuration via .well-known endpoint.")
            return config
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to fetch from .well-known/smart-configuration: {e}. Falling back to /metadata.")
    
    # 2. If the first method fails, fall back to /metadata
    try:
        url = urljoin(fhir_server_url, "metadata")
        logging.info(f"Fetching CapabilityStatement from: {url}")
        response = requests.get(url, headers={'Accept': 'application/json'})
        response.raise_for_status()
        capability_statement = response.json()
        logging.info("Successfully fetched CapabilityStatement.")

        # Traverse the CapabilityStatement to find the SMART URIs
        for rest in capability_statement.get('rest', []):
            security = rest.get('security')
            if security:
                for extension in security.get('extension', []):
                    if extension.get('url') == "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris":
                        auth_uris = {}
                        for ext in extension.get('extension', []):
                            if ext.get('url') == 'authorize':
                                auth_uris['authorization_endpoint'] = ext.get('valueUri')
                            elif ext.get('url') == 'token':
                                auth_uris['token_endpoint'] = ext.get('valueUri')
                        
                        if 'authorization_endpoint' in auth_uris and 'token_endpoint' in auth_uris:
                            logging.info(f"Found SMART URIs in CapabilityStatement: {auth_uris}")
                            return auth_uris
        
        logging.error("Could not find SMART OAuth URIs in CapabilityStatement after fallback.")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch CapabilityStatement from {url}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logging.error(f"Error parsing CapabilityStatement: {e}")
        return None

def render_error_page(title=None, message=None, suggestions=None, status_code=500):
    """Renders the unified error page with a custom message."""
    error_info = {
        'title': title or "An Error Occurred",
        'message': message or "We encountered a problem and couldn't complete your request.",
        'suggestions': suggestions or [
            "Please try relaunching the application from your EHR system.",
            "If the problem persists, please contact support."
        ]
    }
    logging.warning(f"Rendering error page with title: {error_info['title']}")
    return render_template("error.html", error_info=error_info), status_code

def is_session_valid():
    """Checks if the session is valid and contains the necessary FHIR data."""
    required_keys = ['patient', 'server', 'token', 'client_id']
    fhir_data = session.get('fhir_data', {})
    if not all(key in fhir_data and fhir_data[key] for key in required_keys):
        logging.error(f"Session check failed. Missing one or more keys. Current data: {fhir_data}")
        return False
    return True

# --- Core Application Routes ---

@app.route('/launch')
def launch():
    """
    Entry point for the SMART on FHIR launch. It receives the 'iss' and 'launch'
    parameters and redirects the user to the EHR's authorization endpoint.
    """
    iss = request.args.get('iss')
    launch_token = request.args.get('launch')

    if not iss:
        return render_error_page(title="Launch Error", message="'iss' (issuer) parameter is missing.")

    session['launch_params'] = {'iss': iss, 'launch': launch_token}

    smart_config = None
    # Use conditional endpoint discovery
    if 'cerner.com' in iss:
        # --- Hardcoded endpoint discovery for Cerner ---
        logging.info("Cerner issuer detected. Using hardcoded endpoint discovery.")
        try:
            tenant_id = iss.split('/')[-1]
            auth_base_url = "https://authorization.cerner.com/tenants"
            smart_config = {
                "authorization_endpoint": f"{auth_base_url}/{tenant_id}/protocols/oauth2/profiles/smart-v1/personas/provider/authorize",
                "token_endpoint": f"{auth_base_url}/{tenant_id}/protocols/oauth2/profiles/smart-v1/token"
            }
            logging.info(f"Manually constructed Cerner SMART endpoints: {smart_config}")
        except IndexError:
            return render_error_page(title="Configuration Error", message=f"Could not parse tenant_id from Cerner issuer URL: {iss}")
    else:
        # --- Standard discovery for all other issuers (e.g., SMART Health IT) ---
        logging.info("Non-Cerner issuer detected. Using standard SMART discovery.")
        smart_config = get_smart_config(iss)

    if not smart_config:
        return render_error_page(
            title="Configuration Discovery Error",
            message="Could not automatically discover the SMART on FHIR configuration.",
            suggestions=[
                f"Failed to get configuration from the issuer: {iss}",
                "Please check if the EHR server is compliant with SMART on FHIR standards."
            ]
        )

    session['smart_config'] = smart_config
    state = str(uuid.uuid4())
    session['state'] = state

    auth_url = smart_config.get('authorization_endpoint')
    if not auth_url:
        return render_error_page(title="Configuration Error", message="Constructed SMART configuration is missing 'authorization_endpoint'.")

    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "aud": iss
    }
    if launch_token:
        auth_params["launch"] = launch_token
    
    full_auth_url = f"{auth_url}?{urlencode(auth_params)}"
    logging.info(f"Redirecting user to authorization endpoint: {auth_url}")
    return redirect(full_auth_url)

@app.route('/launch/cerner-sandbox')
def launch_cerner_sandbox():
    """
    Direct launch for Cerner sandbox testing without requiring iss parameter.
    This is useful for testing the application with Cerner's sandbox environment.
    """
    logging.info("Launching Cerner sandbox test")
    
    # Use default Cerner sandbox configuration
    iss = CERNER_SANDBOX_CONFIG['fhir_base']
    session['launch_params'] = {'iss': iss, 'launch': None}
    
    smart_config = {
        "authorization_endpoint": CERNER_SANDBOX_CONFIG['authorization_endpoint'],
        "token_endpoint": CERNER_SANDBOX_CONFIG['token_endpoint']
    }
    
    session['smart_config'] = smart_config
    state = str(uuid.uuid4())
    session['state'] = state
    
    auth_params = {
        "response_type": "code", 
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "aud": iss
    }
    
    full_auth_url = f"{smart_config['authorization_endpoint']}?{urlencode(auth_params)}"
    logging.info(f"Redirecting to Cerner sandbox authorization: {full_auth_url}")
    return redirect(full_auth_url)

@app.route('/api/exchange-code', methods=['POST'])
def exchange_code():
    """
    Receives auth code from the frontend, exchanges it for a token, and sets up the session.
    """
    data = request.get_json()
    code = data.get('code')
    received_state = data.get('state')

    session_state = session.pop('state', None)
    if not session_state or received_state != session_state:
        logging.error(f"State mismatch. Expected: {session_state}, Received: {received_state}")
        return jsonify({"status": "error", "error": "State parameter mismatch. Possible CSRF attack."}), 400

    smart_config = session.get('smart_config')
    if not smart_config or 'token_endpoint' not in smart_config:
        return jsonify({"status": "error", "error": "SMART configuration or token endpoint not found in session."}), 400

    token_url = smart_config['token_endpoint']
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID
    }
    
    try:
        response = requests.post(token_url, data=token_params, headers={'Accept': 'application/json'})
        response.raise_for_status()
        token_data = response.json()
        
        session['fhir_data'] = {
            'token': token_data.get('access_token'),
            'patient': token_data.get('patient'),
            'server': session['launch_params']['iss'],
            'client_id': CLIENT_ID
        }
        logging.info("Session data successfully set for patient: " + token_data.get('patient'))
        
        return jsonify({"status": "ok", "redirect_url": url_for('main_page')})

    except requests.exceptions.HTTPError as e:
        error_body = e.response.text
        logging.error(f"Token exchange failed. Status: {e.response.status_code}, Body: {error_body}")
        return jsonify({"status": "error", "error": f"Failed to exchange code. Server responded: {error_body}"}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred during token exchange: {e}", exc_info=True)
        return jsonify({"status": "error", "error": "An unexpected server error occurred."}), 500

@app.route('/callback')
def callback():
    """
    Handles SMART on FHIR OAuth2 callback specifically.
    This route handles the authorization code exchange for SMART apps.
    """
    logging.info("Received request at /callback endpoint")
    
    # Check for authorization errors
    if 'error' in request.args:
        error_type = request.args.get('error')
        error_desc = request.args.get('error_description', 'No description provided.')
        logging.warning(f"Authorization callback failed. Error: {error_type}. Description: {error_desc}")
        return render_error_page(
            title="Authorization Failed",
            message=f"The EHR authorization server returned an error: {error_type.replace('_', ' ').title()}",
            suggestions=[
                "You must grant permission to the application to proceed.",
                "Please try launching the application again from your EHR and approve the request.",
                f"Error details: {error_desc}"
            ],
            status_code=400
        )

    # Check if this is a valid callback with authorization code
    if 'code' in request.args and 'state' in request.args:
        logging.info("Valid authorization code received at /callback. Rendering callback.html for token exchange.")
        return render_template('callback.html')
    
    # If no code parameter, this might be an invalid callback
    logging.warning("Callback endpoint accessed without authorization code")
    return render_error_page(
        title="Invalid Callback", 
        message="This endpoint expects an authorization code from your EHR system.",
        suggestions=[
            "Please launch the application from your EHR system.",
            "If you were redirected here, the authorization may have failed."
        ],
        status_code=400
    )

@app.route('/')
def index():
    """
    Handles the root access, OAuth2 callback, and the initial SMART launch.
    """
    # 1. Check for an explicit denial of access from the auth server
    if 'error' in request.args:
        error_type = request.args.get('error')
        error_desc = request.args.get('error_description', 'No description provided.')
        logging.warning(f"Authorization failed. Error: {error_type}. Description: {error_desc}")
        return render_error_page(
            title="Access Denied",
            message=f"The authorization server returned an error: {error_type.replace('_', ' ').title()}",
            suggestions=[
                "You must grant permission to the application to proceed.",
                "Please try launching the application again from your EHR and approve the request."
            ],
            status_code=403
        )

    # 2. Check if this is the SMART launch from the EHR
    if 'iss' in request.args:
        logging.info("Launch parameter 'iss' found at /. Initiating launch sequence.")
        return launch()

    # 3. Check if this is the OAuth2 callback from the auth server
    if 'code' in request.args and 'state' in request.args:
        logging.info("Reached / with auth code. Rendering callback.html to handle code exchange.")
        return render_template('callback.html')

    # 4. If not a launch or callback, check for an existing session
    if is_session_valid():
        logging.info("Valid session found at /. Redirecting to /main.")
        return redirect(url_for('main_page'))
    
    # 5. If nothing matches, the user needs to launch from EHR
    logging.warning("No session, auth code, or launch parameters found at /. Showing error page.")
    return render_error_page(
        title="Session Not Found", 
        message="Please launch the application from your EHR system.",
        status_code=403
    )

@app.route("/main")
def main_page():
    """Renders the main application page."""
    if not is_session_valid():
        return render_error_page(title="Invalid Session", message="Your session is invalid or has expired.")
    return render_template("main.html")

@app.route("/main_app")
def main_app_page():
    """Renders the main application page with full UI."""
    if not is_session_valid():
        return render_error_page(title="Invalid Session", message="Your session is invalid or has expired.")
    
    fhir_data = session['fhir_data']
    patient_id = fhir_data['patient']
    
    # Get basic patient data for display
    try:
        raw_data, error = get_fhir_data(fhir_data['server'], fhir_data['token'], patient_id, fhir_data['client_id'])
        if error:
            logging.warning(f"Error fetching patient data for main_app: {error}")
            patient_data = None
            patient_name_display = None
        else:
            patient_data = raw_data.get("patient")
            demographics = get_patient_demographics(patient_data)
            patient_name_display = demographics.get('name', 'Unknown')
    except Exception as e:
        logging.error(f"Error in main_app_page: {e}")
        patient_data = None
        patient_name_display = None
    
    return render_template("main_app.html", 
                         patient_data=patient_data,
                         patient_name_display=patient_name_display)

@app.route("/calculate_risk")
def calculate_risk():
    """Renders the risk calculation UI page."""
    if not is_session_valid():
        return render_error_page(title="Invalid Session", message="Your session is invalid or has expired.")
    
    fhir_data = session['fhir_data']
    patient_id = fhir_data['patient']
    
    try:
        # Get FHIR data and calculate risk
        raw_data, error = get_fhir_data(fhir_data['server'], fhir_data['token'], patient_id, fhir_data['client_id'])
        if error:
            logging.error(f"Error fetching FHIR data for risk calculation: {error}")
            return render_error_page(title="Data Error", message=f"Failed to retrieve data: {error}")

        # Get patient demographics
        demographics = get_patient_demographics(raw_data.get("patient"))
        
        # Calculate risk components and total score
        components, total_score = calculate_risk_components(raw_data, demographics)
        
        # Get risk categories from config
        risk_categories = CDSS_CONFIG.get('risk_categories', {})
        
        # Determine risk category based on PRECISE-DAPT thresholds
        if total_score >= risk_categories.get('high_risk', {}).get('min_score', 25):
            risk_category = 'High Bleeding Risk'
        elif total_score >= risk_categories.get('moderate_risk', {}).get('min_score', 16):
            risk_category = 'Moderate Bleeding Risk'
        elif total_score >= risk_categories.get('low_risk', {}).get('min_score', 8):
            risk_category = 'Low Bleeding Risk'
        else:
            risk_category = 'Very Low Bleeding Risk'
        
        # Create detailed calculation structure for the UI (PRECISE-DAPT format)
        calculation_details = {
            'age': demographics.get('age'),
            'sex': demographics.get('gender'),
            'score': total_score,
            'category': risk_category,
            'hb_value': None,
            'ccr_value': None,
            'wbc_value': None,
            'bleeding_history': False,
            'score_details': {
                'age_score_component': 0,
                'hemoglobin_score_component': 0,
                'creatinine_clearance_score_component': 0,
                'wbc_score_component': 0,
                'bleeding_history_score_component': 0
            }
        }
        
        # Extract specific values from components for PRECISE-DAPT
        for component in components:
            parameter = component.get('parameter', '').lower()
            score = component.get('score', 0)
            value_str = component.get('value', '')
            
            # Age component
            if 'precisedapt - age' in parameter:
                calculation_details['score_details']['age_score_component'] = score
            
            # Hemoglobin component
            elif 'precisedapt - hemoglobin' in parameter:
                calculation_details['score_details']['hemoglobin_score_component'] = score
                # Extract Hb value
                try:
                    hb_match = value_str.split()[0]
                    calculation_details['hb_value'] = float(hb_match)
                except:
                    pass
            
            # Creatinine Clearance component
            elif 'precisedapt - creatinine clearance' in parameter:
                calculation_details['score_details']['creatinine_clearance_score_component'] = score
                # Extract CCr value
                try:
                    ccr_match = value_str.split()[0]
                    calculation_details['ccr_value'] = float(ccr_match)
                except:
                    pass
            
            # White Blood Cell Count component
            elif 'precisedapt - white blood cell count' in parameter:
                calculation_details['score_details']['wbc_score_component'] = score
                # Extract WBC value
                try:
                    wbc_match = value_str.split()[0]
                    calculation_details['wbc_value'] = float(wbc_match)
                except:
                    pass
            
            # Previous Bleeding component
            elif 'precisedapt - prior bleeding' in parameter:
                calculation_details['score_details']['bleeding_history_score_component'] = score
                calculation_details['bleeding_history'] = score > 0
        
        return render_template("calculate_risk_ui.html",
                             title="Bleeding Risk Assessment",
                             patient_id=patient_id,
                             calculation_details=calculation_details,
                             risk_components=components,
                             config_version=CDSS_CONFIG.get('version', '1.2.0'))
                             
    except Exception as e:
        logging.error(f"Error in calculate_risk: {e}", exc_info=True)
        return render_error_page(title="Calculation Error", message=f"An error occurred during risk calculation: {str(e)}")

@app.route('/api/calculate_risk')
def calculate_risk_api():
    """API endpoint to fetch FHIR data and calculate risk."""
    if not is_session_valid():
        return jsonify({"error": "Session is invalid or expired. Please re-launch the app."}), 400

    fhir_data = session['fhir_data']
    patient_id = fhir_data['patient']
    fhir_server_url = fhir_data['server']
    access_token = fhir_data['token']
    client_id = fhir_data['client_id']
    
    # Add detailed logging for debugging
    logging.info(f"=== API Calculate Risk Debug Info ===")
    logging.info(f"Patient ID: {patient_id}")
    logging.info(f"FHIR Server URL: {fhir_server_url}")
    logging.info(f"Client ID: {client_id}")
    logging.info(f"Access Token Length: {len(access_token) if access_token else 'None'}")
    logging.info(f"Access Token Preview: {access_token[:50]}..." if access_token else "No token")
    
    try:
        # 1. Get raw FHIR resources
        raw_data, error = get_fhir_data(fhir_server_url, access_token, patient_id, client_id)
        if error:
            logging.error(f"Error fetching FHIR data: {error}")
            return jsonify({"error": "Failed to retrieve data from FHIR server.", "details": str(error)}), 500

        # 2. Get patient demographics
        demographics = get_patient_demographics(raw_data.get("patient"))

        # 3. Calculate risk components and total score
        components, total_score = calculate_risk_components(raw_data, demographics)

        # 4. Determine risk level based on PRECISE-DAPT thresholds from config
        risk_categories = CDSS_CONFIG.get('risk_categories', {})
        
        if total_score >= risk_categories.get('high_risk', {}).get('min_score', 25):
            risk_level = 'High Bleeding Risk (PRECISE-DAPT ≥25)'
            recommendation = risk_categories.get('high_risk', {}).get('recommendation', 
                'High bleeding risk. Consider shorter DAPT duration (3-6 months).')
        elif total_score >= risk_categories.get('moderate_risk', {}).get('min_score', 16):
            risk_level = 'Moderate Bleeding Risk (PRECISE-DAPT 16-24)'
            recommendation = risk_categories.get('moderate_risk', {}).get('recommendation',
                'Moderate bleeding risk. Standard DAPT duration with careful monitoring.')
        elif total_score >= risk_categories.get('low_risk', {}).get('min_score', 8):
            risk_level = 'Low Bleeding Risk (PRECISE-DAPT 8-15)'
            recommendation = risk_categories.get('low_risk', {}).get('recommendation',
                'Low bleeding risk. Standard DAPT duration (12 months) recommended.')
        else:
            risk_level = 'Very Low Bleeding Risk (PRECISE-DAPT 0-7)'
            recommendation = risk_categories.get('very_low_risk', {}).get('recommendation',
                'Very low bleeding risk. Extended DAPT duration may be considered.')

        # 5. Assemble the final response
        response_data = {
            "patient_info": demographics,
            "score_components": components,
            "total_score": total_score,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "scoring_system": {
                "version": CDSS_CONFIG.get('version', '1.2.0'),
                "source": CDSS_CONFIG.get('guideline_source', 'PRECISE-DAPT 2017'),
                "description": "PRECISE-DAPT score: ≥25 = high bleeding risk"
            }
        }
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error in /api/calculate_risk: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/logout")
def logout():
    """Clears the session and redirects to a logged-out message page."""
    session.clear()
    return render_error_page(
        title="Logged Out",
        message="You have been successfully logged out.",
        suggestions=["You can now close this window or re-launch the app from your EHR."],
        status_code=200
    )

# Serve static files for local development
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    """Serves favicon.ico to prevent 404 errors."""
    try:
        return send_from_directory('static', 'favicon.ico')
    except FileNotFoundError:
        # Return a minimal response if favicon doesn't exist
        from flask import Response
        return Response(status=204)  # No Content

# --- Main Execution ---
if __name__ == '__main__':
    # This is used when running locally. When deploying, Gunicorn is used.
    app.run(host="127.0.0.1", port=8080, debug=True) 