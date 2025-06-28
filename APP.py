import os
import json
import logging
import uuid
import requests
from datetime import datetime
from urllib.parse import urljoin, urlencode
from dotenv import load_dotenv

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, session, jsonify, url_for, render_template_string)
from flask_session import Session
from flask_cors import CORS

from fhir_data_service import get_fhir_data, calculate_risk_components, get_patient_demographics, CDSS_CONFIG

# --- App Initialization & Configuration ---

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Enable CORS for CDS Hooks endpoints
CORS(app, resources={
    r"/cds-services*": {"origins": "*"},
    r"/api/*": {"origins": "*"}
})

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
CLIENT_ID = os.environ.get('SMART_CLIENT_ID', '293d1535-87b4-439c-b512-db7e30975833')
# The redirect_uri must be the full URL to the /callback endpoint
# It's crucial that this matches the registration EXACTLY.
REDIRECT_URI = os.environ.get('SMART_REDIRECT_URI', 'http://127.0.0.1:8080/callback').strip()
# Remove any comments or extra text that might have been accidentally added
if '#' in REDIRECT_URI:
    REDIRECT_URI = REDIRECT_URI.split('#')[0].strip()
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

# Debug logging for configuration
logging.info(f"CLIENT_ID: {CLIENT_ID}")
logging.info(f"REDIRECT_URI: '{REDIRECT_URI}' (length: {len(REDIRECT_URI)})")
logging.info(f"REDIRECT_URI repr: {repr(REDIRECT_URI)}")

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

@app.before_request
def fix_callback_url():
    """Fix callback URLs that have encoded spaces due to EHR issues."""
    if request.path.startswith('/callback%20'):
        # Redirect to the clean callback URL with all query parameters
        from flask import redirect, url_for
        return redirect(url_for('callback', **request.args))

@app.route('/callback<path:extra>', methods=['GET', 'POST'])
@app.route('/callback', methods=['GET', 'POST'])
def callback(extra=None):
    """
    Handles SMART on FHIR OAuth2 callback specifically.
    This route handles the authorization code exchange for SMART apps.
    """
    logging.info("=== CALLBACK ENDPOINT REACHED ===")
    logging.info(f"Extra path parameter: {extra}")
    logging.info(f"Request path: {request.path}")
    logging.info(f"Request full path: {request.full_path}")
    logging.info(f"Request URL: {request.url}")
    logging.info(f"Request args: {dict(request.args)}")
    logging.info(f"Request method: {request.method}")
    
    # Handle the case where there's extra text in the callback URL
    if extra and extra.strip():
        logging.warning(f"Callback received with extra path: '{extra}' - this suggests a configuration issue")
        logging.warning("The REDIRECT_URI might contain extra characters or spaces")
    
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
    if 'code' in request.args:
        state_param = request.args.get('state')
        code_param = request.args.get('code')
        
        logging.info(f"Authorization code received: {code_param[:50]}...")
        logging.info(f"State parameter: {state_param}")
        
        # Even if state is missing from session (due to restart), we can still process
        if state_param:
            logging.info("Valid authorization code with state received at /callback. Rendering callback.html for token exchange.")
        else:
            logging.warning("Authorization code received but no state parameter. Proceeding anyway.")
            
        return render_template('callback.html')
    
    # If no code parameter, this might be an invalid callback
    logging.warning("Callback endpoint accessed without authorization code")
    logging.warning(f"Available parameters: {list(request.args.keys())}")
    
    return render_error_page(
        title="Invalid Callback", 
        message="This endpoint expects an authorization code from your EHR system.",
        suggestions=[
            "Please launch the application from your EHR system.",
            "If you were redirected here, the authorization may have failed.",
            f"Available parameters: {list(request.args.keys())}"
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
    
    fhir_data = session['fhir_data']
    patient_id = fhir_data['patient']
    
    return render_template("main.html", patient_id=patient_id)

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
        
        # Determine risk category based on PRECISE-DAPT thresholds (3-tier system)
        if total_score >= risk_categories.get('high_risk', {}).get('min_score', 25):
            risk_category = 'High Bleeding Risk'
        elif total_score >= risk_categories.get('moderate_risk', {}).get('min_score', 16):
            risk_category = 'Moderate Bleeding Risk'
        else:
            risk_category = 'Low Bleeding Risk'
        
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

        # 4. Determine risk level based on PRECISE-DAPT thresholds from config (3-tier system)
        risk_categories = CDSS_CONFIG.get('risk_categories', {})
        
        if total_score >= risk_categories.get('high_risk', {}).get('min_score', 25):
            risk_level = 'High Bleeding Risk (PRECISE-DAPT ≥25)'
            recommendation = risk_categories.get('high_risk', {}).get('recommendation', 
                'High bleeding risk. Consider shorter DAPT duration (3-6 months).')
        elif total_score >= risk_categories.get('moderate_risk', {}).get('min_score', 16):
            risk_level = 'Moderate Bleeding Risk (PRECISE-DAPT 16-24)'
            recommendation = risk_categories.get('moderate_risk', {}).get('recommendation',
                'Moderate bleeding risk. Standard DAPT duration with careful monitoring.')
        else:
            risk_level = 'Low Bleeding Risk (PRECISE-DAPT 0-15)'
            recommendation = risk_categories.get('low_risk', {}).get('recommendation',
                'Low bleeding risk. Standard DAPT duration (12 months) recommended.')

        # 5. Assemble the final response with patient_id
        patient_info = demographics.copy()
        patient_info['patient_id'] = patient_id  # Add patient_id to the response
        
        response_data = {
            "patient_info": patient_info,
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

# --- Feedback System Routes ---

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit user feedback on calculation results.
    Accepts thumbs up/down feedback and optional comments.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract feedback data
        patient_id = data.get('patient_id')
        feedback_type = data.get('feedback_type')  # 'thumbs_up' or 'thumbs_down'
        comment = data.get('comment', '')
        score = data.get('score')
        risk_level = data.get('risk_level')
        
        # Validate required fields
        if not patient_id or not feedback_type:
            return jsonify({"error": "patient_id and feedback_type are required"}), 400
        
        if feedback_type not in ['thumbs_up', 'thumbs_down']:
            return jsonify({"error": "feedback_type must be 'thumbs_up' or 'thumbs_down'"}), 400
        
        # Create feedback record
        feedback_record = {
            'patient_id': patient_id,
            'feedback_type': feedback_type,
            'comment': comment,
            'score': score,
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat(),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr
        }
        
        # Log the feedback (in production, you might save to database)
        logging.info(f"User feedback received: {feedback_record}")
        
        # For now, we'll just store in session as an example
        # In production, you would save to a database
        if 'feedback_history' not in session:
            session['feedback_history'] = []
        session['feedback_history'].append(feedback_record)
        
        return jsonify({
            "status": "success",
            "message": "感謝您的回饋！您的意見對我們改進計算結果很重要。",
            "feedback_id": str(uuid.uuid4())
        })
        
    except Exception as e:
        logging.error(f"Error in submit_feedback: {e}", exc_info=True)
        return jsonify({"error": "Failed to submit feedback"}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """
    Get feedback statistics (for admin/debugging purposes).
    """
    try:
        feedback_history = session.get('feedback_history', [])
        
        # Calculate basic stats
        total_feedback = len(feedback_history)
        thumbs_up = sum(1 for f in feedback_history if f['feedback_type'] == 'thumbs_up')
        thumbs_down = sum(1 for f in feedback_history if f['feedback_type'] == 'thumbs_down')
        
        stats = {
            'total_feedback': total_feedback,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'satisfaction_rate': (thumbs_up / total_feedback * 100) if total_feedback > 0 else 0
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error in get_feedback_stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to get feedback stats"}), 500

# Serve static files for local development
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    """Serves favicon.ico using the app logo."""
    try:
        return send_from_directory('static', 'favicon.ico')
    except FileNotFoundError:
        # Return SVG favicon using our logo design
        from flask import Response
        svg_favicon = '''<svg width="32" height="32" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
            <circle cx="128" cy="128" r="118" fill="#f0f9ff" stroke="#2563eb" stroke-width="12"/>
            <path d="M 70 128 A 58 58 0 0 1 186 128" fill="none" stroke-width="20" stroke="url(#faviconGrad)" stroke-linecap="round"/>
            <circle cx="85" cy="145" r="10" fill="#10b981"/>
            <circle cx="128" cy="75" r="10" fill="#f59e0b"/>
            <circle cx="171" cy="145" r="10" fill="#ef4444"/>
            <path d="M128 90 C115 77, 95 77, 95 95 C95 115, 128 145, 128 145 C128 145, 161 115, 161 95 C161 77, 141 77, 128 90 Z" fill="#dc2626"/>
            <defs>
                <linearGradient id="faviconGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#10b981"/>
                    <stop offset="50%" style="stop-color:#f59e0b"/>
                    <stop offset="100%" style="stop-color:#ef4444"/>
                </linearGradient>
            </defs>
        </svg>'''
        return Response(svg_favicon, mimetype='image/svg+xml')

@app.route('/test-callback')
def test_callback():
    """Test endpoint to verify routing works."""
    return jsonify({
        "status": "success",
        "message": "Test callback endpoint working - UPDATED VERSION",
        "timestamp": "2025-06-13",
        "version": "20250613t000058+",
        "args": dict(request.args)
    })

@app.route('/callback-debug')
def callback_debug():
    """Debug version of callback with extra logging."""
    logging.info("=== CALLBACK DEBUG ENDPOINT ===")
    logging.info(f"Request URL: {request.url}")
    logging.info(f"Request args: {dict(request.args)}")
    logging.info(f"Request method: {request.method}")
    logging.info(f"User agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    # Check if this is a valid callback with authorization code
    if 'code' in request.args:
        state_param = request.args.get('state')
        code_param = request.args.get('code')
        
        logging.info(f"DEBUG: Authorization code received: {code_param[:50]}...")
        logging.info(f"DEBUG: State parameter: {state_param}")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Callback Debug - WORKING</title></head>
        <body>
            <h1>✅ Callback Debug - WORKING!</h1>
            <p><strong>Code:</strong> {code_param[:50]}...</p>
            <p><strong>State:</strong> {state_param}</p>
            <p><strong>Version:</strong> 20250613t000058+</p>
            <p><strong>Time:</strong> {request.args}</p>
            <hr>
            <p>This confirms the callback endpoint is working correctly.</p>
            <script>
                console.log('Callback debug page loaded successfully');
                console.log('Code:', '{code_param[:50]}...');
                console.log('State:', '{state_param}');
            </script>
        </body>
        </html>
        """
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Callback Debug - No Code</title></head>
    <body>
        <h1>⚠️ Callback Debug - No Authorization Code</h1>
        <p><strong>Available parameters:</strong> {list(request.args.keys())}</p>
        <p><strong>All args:</strong> {dict(request.args)}</p>
        <p><strong>Version:</strong> 20250613t000058+</p>
    </body>
    </html>
    """

# --- CDS Hooks Implementation ---

def check_dapt_medications(medications):
    """
    Check if patient is on dual antiplatelet therapy (DAPT) with specific combinations:
    - aspirin + clopidogrel
    - aspirin + prasugrel  
    - aspirin + ticagrelor
    
    Returns: (has_dapt, medications_found)
    """
    # Define medication mappings (RxNorm codes and common names)
    aspirin_codes = {
        'rxnorm': ['1191', '1154070', '1154071'],  # aspirin RxNorm codes
        'names': ['aspirin', 'acetylsalicylic acid', 'asa']
    }
    
    antiplatelet_agents = {
        'clopidogrel': {
            'rxnorm': ['32968', '309362'],
            'names': ['clopidogrel', 'plavix']
        },
        'prasugrel': {
            'rxnorm': ['861634', '861635'],
            'names': ['prasugrel', 'effient']
        },
        'ticagrelor': {
            'rxnorm': ['1116632', '1116635'],
            'names': ['ticagrelor', 'brilinta']
        }
    }
    
    found_meds = {'aspirin': False, 'antiplatelet': None}
    medication_details = []
    
    for med in medications:
        if not med or 'medicationCodeableConcept' not in med:
            continue
            
        # Extract medication information
        med_concept = med['medicationCodeableConcept']
        med_name = ""
        med_codes = []
        
        # Get display name
        if 'text' in med_concept:
            med_name = med_concept['text'].lower()
        
        # Get coding information
        for coding in med_concept.get('coding', []):
            if coding.get('system') == 'http://www.nlm.nih.gov/research/umls/rxnorm':
                med_codes.append(coding.get('code', ''))
            if coding.get('display'):
                med_name += ' ' + coding.get('display', '').lower()
        
        # Check for aspirin
        aspirin_found = False
        for code in med_codes:
            if code in aspirin_codes['rxnorm']:
                aspirin_found = True
                break
        
        if not aspirin_found:
            for name in aspirin_codes['names']:
                if name in med_name:
                    aspirin_found = True
                    break
        
        if aspirin_found:
            found_meds['aspirin'] = True
            medication_details.append({
                'name': 'Aspirin',
                'original_name': med_concept.get('text', 'Aspirin'),
                'status': med.get('status', 'unknown')
            })
        
        # Check for antiplatelet agents
        for agent_name, agent_info in antiplatelet_agents.items():
            agent_found = False
            
            # Check by RxNorm code
            for code in med_codes:
                if code in agent_info['rxnorm']:
                    agent_found = True
                    break
            
            # Check by name
            if not agent_found:
                for name in agent_info['names']:
                    if name in med_name:
                        agent_found = True
                        break
            
            if agent_found:
                found_meds['antiplatelet'] = agent_name
                medication_details.append({
                    'name': agent_name.title(),
                    'original_name': med_concept.get('text', agent_name.title()),
                    'status': med.get('status', 'unknown')
                })
                break
    
    has_dapt = found_meds['aspirin'] and found_meds['antiplatelet'] is not None
    
    return has_dapt, medication_details

def create_dapt_warning_card(patient_name, precise_dapt_score, medications_found):
    """Create a CDS Hooks card for DAPT high bleeding risk warning."""
    
    medication_list = ", ".join([med['name'] for med in medications_found])
    
    card = {
        "summary": f"🚨 HIGH BLEEDING RISK: Patient on DAPT with PRECISE-DAPT score {precise_dapt_score}",
        "detail": f"""Patient {patient_name} is currently on dual antiplatelet therapy ({medication_list}) and has a **HIGH BLEEDING RISK**.

**PRECISE-DAPT Score: {precise_dapt_score} (≥25 = High Risk)**

🔴 **CLINICAL RECOMMENDATIONS:**
• Consider shorter DAPT duration (3-6 months instead of 12 months)
• Close monitoring for bleeding events
• Evaluate use of proton pump inhibitors (PPIs)
• Regular hemoglobin and renal function monitoring
• Consider cardiology consultation for individualized treatment strategy

**Risk Assessment Details:**
This alert is triggered when patients are on specific DAPT combinations (aspirin + clopidogrel/prasugrel/ticagrelor) AND have high bleeding risk (PRECISE-DAPT ≥25).
        """,
        "indicator": "critical",
        "source": {
            "label": "PRECISE-DAPT Bleeding Risk Calculator",
            "url": "https://www.precisedapttool.com"
        },
        "suggestions": [
            {
                "label": "View Detailed Risk Assessment",
                "actions": [
                    {
                        "type": "create",
                        "description": "Launch detailed PRECISE-DAPT risk calculator",
                        "resource": {
                            "resourceType": "ServiceRequest",
                            "status": "draft",
                            "intent": "proposal",
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://loinc.org",
                                        "code": "LA-PRECISE-DAPT",
                                        "display": "PRECISE-DAPT Bleeding Risk Assessment"
                                    }
                                ]
                            },
                            "subject": {
                                "reference": f"Patient/{patient_name}"
                            }
                        }
                    }
                ]
            },
            {
                "label": "Consider PPI Co-prescription",
                "actions": [
                    {
                        "type": "create", 
                        "description": "Consider proton pump inhibitor for GI protection",
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "status": "draft",
                            "intent": "proposal",
                            "medicationCodeableConcept": {
                                "coding": [
                                    {
                                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                        "code": "40790",
                                        "display": "omeprazole"
                                    }
                                ],
                                "text": "Omeprazole 20mg once daily"
                            }
                        }
                    }
                ]
            }
        ]
    }
    
    return card

@app.route('/cds-services', methods=['GET'])
def cds_services_discovery():
    """CDS Hooks service discovery endpoint."""
    try:
        # Try multiple possible paths with more comprehensive search
        current_dir = os.getcwd()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        possible_paths = [
            'cds-services.json',  # Current directory
            os.path.join(script_dir, 'cds-services.json'),  # Script directory
            '/app/cds-services.json',  # App Engine typical path
            './cds-services.json',  # Explicit relative path
            os.path.join('/workspace', 'cds-services.json'),  # Workspace path (for some deployment environments)
            os.path.join(current_dir, 'cds-services.json')  # Explicit current directory
        ]
        
        # Enhanced logging for debugging
        logging.info(f"=== CDS Services Discovery Debug Info ===") 
        logging.info(f"Current working directory: {current_dir}")
        logging.info(f"Script file location: {os.path.abspath(__file__)}")
        logging.info(f"Script directory: {script_dir}")
        
        # Try to list directory contents with better error handling
        try:
            files = os.listdir(current_dir)
            json_files = [f for f in files if f.endswith('.json')]
            logging.info(f"JSON files in current directory: {json_files}")
            if 'cds-services.json' in json_files:
                logging.info("✓ cds-services.json found in current directory listing")
            else:
                logging.warning("✗ cds-services.json NOT found in current directory listing")
        except Exception as e:
            logging.error(f"Cannot list current directory: {e}")
        
        # Try script directory as well
        try:
            if script_dir != current_dir:
                script_files = os.listdir(script_dir)
                script_json_files = [f for f in script_files if f.endswith('.json')]
                logging.info(f"JSON files in script directory: {script_json_files}")
        except Exception as e:
            logging.error(f"Cannot list script directory: {e}")
        
        config_data = None
        used_path = None
        
        for path in possible_paths:
            logging.info(f"Trying path: {path}")
            try:
                if os.path.exists(path):
                    logging.info(f"✓ File exists at: {path}")
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        used_path = path
                        logging.info(f"✓ Successfully loaded config from: {path}")
                        break
                    except Exception as e:
                        logging.error(f"✗ Error reading file at {path}: {e}")
                else:
                    logging.info(f"✗ File not found at: {path}")
            except Exception as e:
                logging.error(f"✗ Error checking path {path}: {e}")
        
        if config_data:
            logging.info(f"Successfully loaded CDS services config from: {used_path}")
            logging.info(f"Config contains {len(config_data.get('services', []))} services")
            return jsonify(config_data)
        else:
            # Return a hardcoded fallback - this ensures the service always works
            logging.warning("All file paths failed - using hardcoded fallback CDS services config")
            fallback_config = {
                "services": [
                    {
                        "hook": "medication-prescribe",
                        "id": "dapt_bleeding_risk_alert",
                        "title": "DAPT High Bleeding Risk Alert",
                        "description": "Alert for patients on dual antiplatelet therapy (DAPT) with high bleeding risk (PRECISE-DAPT ≥25)",
                        "prefetch": {
                            "patient": "Patient/{{context.patientId}}",
                            "medications": "MedicationRequest?patient={{context.patientId}}&status=active&_count=50",
                            "hemoglobin": "Observation?patient={{context.patientId}}&code=718-7&_sort=-date&_count=1",
                            "creatinine": "Observation?patient={{context.patientId}}&code=2160-0&_sort=-date&_count=1",
                            "egfr": "Observation?patient={{context.patientId}}&code=33914-3&_sort=-date&_count=1",
                            "wbc": "Observation?patient={{context.patientId}}&code=26464-8,6690-2,33256-9&_sort=-date&_count=1",
                            "conditions": "Condition?patient={{context.patientId}}&_count=100"
                        }
                    }
                ]
            }
            return jsonify(fallback_config)
            
    except Exception as e:
        logging.error(f"Unexpected error in CDS services discovery: {e}", exc_info=True)
        # Even in case of complete failure, return a minimal working config
        emergency_config = {
            "services": [
                {
                    "hook": "medication-prescribe",
                    "id": "dapt_bleeding_risk_alert",
                    "title": "DAPT High Bleeding Risk Alert",
                    "description": "Alert for patients on dual antiplatelet therapy (DAPT) with high bleeding risk"
                }
            ]
        }
        return jsonify(emergency_config)

@app.route('/cds-services/dapt_bleeding_risk_alert', methods=['POST'])
def dapt_bleeding_risk_alert():
    """
    CDS Hooks endpoint for DAPT high bleeding risk alerts in medication prescribing workflow.
    """
    return handle_dapt_bleeding_risk_hook()

@app.route('/cds-services/dapt_bleeding_risk_patient_view', methods=['POST'])
def dapt_bleeding_risk_patient_view():
    """
    CDS Hooks endpoint for DAPT high bleeding risk alerts in patient view.
    """
    return handle_dapt_bleeding_risk_hook()

def handle_dapt_bleeding_risk_hook():
    """
    Shared handler for DAPT high bleeding risk alerts.
    
    Triggers when:
    1. Patient is on DAPT (aspirin + clopidogrel/prasugrel/ticagrelor)
    2. Patient has high bleeding risk (PRECISE-DAPT ≥25)
    
    Used by both medication-prescribe and patient-view hooks.
    """
    try:
        # Parse the CDS Hooks request
        hook_request = request.get_json()
        
        if not hook_request:
            return jsonify({"cards": []}), 400
        
        # Extract context and prefetch data
        context = hook_request.get('context', {})
        prefetch = hook_request.get('prefetch', {})
        
        patient_id = context.get('patientId')
        if not patient_id:
            logging.warning("No patientId in CDS Hooks request context")
            return jsonify({"cards": []})
        
        # Get patient information
        patient_data = prefetch.get('patient')
        patient_name = "Patient"
        if patient_data:
            name_data = patient_data.get('name', [{}])[0]
            given = " ".join(name_data.get('given', []))
            family = name_data.get('family', "")
            patient_name = f"{given} {family}".strip() or patient_id
        
        # Check medications for DAPT
        medications = prefetch.get('medications', {}).get('entry', [])
        medication_resources = [entry.get('resource') for entry in medications if entry.get('resource')]
        
        has_dapt, dapt_medications = check_dapt_medications(medication_resources)
        
        if not has_dapt:
            logging.info(f"Patient {patient_id} not on DAPT - no alert needed")
            return jsonify({"cards": []})
        
        logging.info(f"Patient {patient_id} is on DAPT: {[med['name'] for med in dapt_medications]}")
        
        # Calculate PRECISE-DAPT score using prefetch data
        try:
            # Transform prefetch data to match our existing format
            raw_data = {
                'patient': patient_data,
                'HEMOGLOBIN': [],
                'CREATININE': [],
                'EGFR': [],
                'WBC': [],
                'conditions': []
            }
            
            # Process observations
            for obs_type, obs_key in [('HEMOGLOBIN', 'hemoglobin'), ('CREATININE', 'creatinine'), 
                                     ('EGFR', 'egfr'), ('WBC', 'wbc')]:
                obs_data = prefetch.get(obs_key, {})
                if obs_data.get('entry'):
                    raw_data[obs_type] = [entry['resource'] for entry in obs_data['entry']]
            
            # Process conditions
            conditions_data = prefetch.get('conditions', {})
            if conditions_data.get('entry'):
                raw_data['conditions'] = [entry['resource'] for entry in conditions_data['entry']]
            
            # Calculate risk
            demographics = get_patient_demographics(patient_data)
            components, total_score = calculate_risk_components(raw_data, demographics)
            
            # Check if high risk (≥25)
            if total_score >= 25:
                logging.info(f"Patient {patient_id} has HIGH bleeding risk (PRECISE-DAPT: {total_score}) and is on DAPT - triggering alert")
                
                warning_card = create_dapt_warning_card(patient_name, total_score, dapt_medications)
                
                return jsonify({
                    "cards": [warning_card]
                })
            else:
                logging.info(f"Patient {patient_id} on DAPT but bleeding risk not high (PRECISE-DAPT: {total_score}) - no alert")
                return jsonify({"cards": []})
                
        except Exception as calc_error:
            logging.error(f"Error calculating PRECISE-DAPT score for CDS Hook: {calc_error}")
            # Return a generic warning card if calculation fails
            generic_card = {
                "summary": "Patient on DAPT - Consider Bleeding Risk Assessment",
                "detail": f"Patient {patient_name} is on dual antiplatelet therapy ({', '.join([med['name'] for med in dapt_medications])}). Consider evaluating bleeding risk using PRECISE-DAPT score.",
                "indicator": "info",
                "source": {
                    "label": "PRECISE-DAPT Bleeding Risk Calculator"
                }
            }
            return jsonify({"cards": [generic_card]})
        
    except Exception as e:
        logging.error(f"Error in DAPT bleeding risk CDS Hook: {e}", exc_info=True)
        return jsonify({"cards": []}), 500

# --- Debug Route for Patient ID ---
@app.route('/debug/patient-id')
def debug_patient_id():
    """Debug route to check patient_id in session."""
    try:
        if not session.get('fhir_data'):
            return f"""
            <h1>Debug: No FHIR Data in Session</h1>
            <p>Session keys: {list(session.keys())}</p>
            <p>Please launch from EHR first.</p>
            """
        
        fhir_data = session['fhir_data']
        patient_id = fhir_data.get('patient', 'NOT_FOUND')
        
        return f"""
        <h1>Debug: Patient ID Test</h1>
        <p><strong>Patient ID:</strong> <span style="background: blue; color: white; padding: 5px; border-radius: 3px;">{patient_id}</span></p>
        <p><strong>FHIR Data Keys:</strong> {list(fhir_data.keys())}</p>
        <p><strong>Server:</strong> {fhir_data.get('server', 'NOT_FOUND')}</p>
        <p><strong>Client ID:</strong> {fhir_data.get('client_id', 'NOT_FOUND')}</p>
        <hr>
        <a href="/main">Go to Main Page</a>
        """
    except Exception as e:
        return f"""
        <h1>Debug: Error</h1>
        <p>Error: {str(e)}</p>
        <p>Session: {dict(session)}</p>
        """

# --- Test Route for Patient ID Template ---
@app.route('/test/patient-id')
def test_patient_id():
    """Test route to debug Patient ID display."""
    if not is_session_valid():
        return render_error_page(title="Invalid Session", message="Your session is invalid or has expired.")
    
    fhir_data = session['fhir_data']
    patient_id = fhir_data['patient']
    
    return render_template("test_patient_id.html", patient_id=patient_id)

# --- Landing Page Route ---

@app.route('/landing')
@app.route('/about')
@app.route('/info')
def landing_page():
    """
    Serves the informational landing page that describes the app,
    its purpose, and how it works. This is useful for:
    - Documentation and information
    - Integration teams who want to understand the app
    - Clinical teams evaluating the tool
    - Public information about the PRECISE-DAPT calculator
    """
    try:
        # Serve the static landing page
        return send_from_directory('.', 'landing_page.html')
    except FileNotFoundError:
        # Fallback: create a simple landing page in case file is missing
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PRECISE-DAPT Bleeding Risk Calculator</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
                .header { text-align: center; background: #f8f9fa; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
                .card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
                .btn { display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🩸 PRECISE-DAPT Bleeding Risk Calculator</h1>
                <p>Advanced Clinical Decision Support for Dual Antiplatelet Therapy</p>
            </div>
            
            <div class="card">
                <h2>📋 What is PRECISE-DAPT?</h2>
                <p>The PRECISE-DAPT bleeding risk calculator is a validated clinical decision support tool that helps clinicians assess bleeding risk in patients on dual antiplatelet therapy (DAPT).</p>
                
                <h3>Key Features:</h3>
                <ul>
                    <li><strong>Evidence-Based:</strong> Based on large clinical trials (Circulation 2017)</li>
                    <li><strong>SMART on FHIR:</strong> Seamlessly integrates with EHR systems</li>
                    <li><strong>Automated:</strong> Pulls data directly from patient records</li>
                    <li><strong>Real-time Alerts:</strong> CDS Hooks for clinical decision support</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>🎯 Clinical Purpose</h2>
                <p>This tool calculates bleeding risk for patients on DAPT using five clinical parameters:</p>
                <ul>
                    <li>Age</li>
                    <li>Hemoglobin level</li>
                    <li>Creatinine clearance</li>
                    <li>White blood cell count</li>
                    <li>Prior bleeding history</li>
                </ul>
                
                <h3>Risk Stratification:</h3>
                <ul>
                    <li><strong>Low Risk (0-15):</strong> Standard DAPT duration (12 months)</li>
                    <li><strong>Moderate Risk (16-24):</strong> Careful monitoring recommended</li>
                    <li><strong>High Risk (≥25):</strong> Consider shorter DAPT duration (3-6 months)</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>⚡ Technical Integration</h2>
                <p>Built using modern healthcare interoperability standards:</p>
                <ul>
                    <li><strong>FHIR R4:</strong> Standard healthcare data format</li>
                    <li><strong>SMART on FHIR:</strong> Secure EHR integration</li>
                    <li><strong>CDS Hooks:</strong> Real-time clinical decision support</li>
                    <li><strong>OAuth2:</strong> Secure authentication</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>🚀 Get Started</h2>
                <p>Ready to integrate PRECISE-DAPT into your clinical workflow?</p>
                <a href="/launch/cerner-sandbox" class="btn">Try Cerner Sandbox Demo</a>
                <a href="/main" class="btn" style="background: #6c757d;">View Documentation</a>
            </div>
            
            <div class="card">
                <h2>📞 Support & Integration</h2>
                <p>For technical integration support or clinical questions:</p>
                <ul>
                    <li><strong>Compatible EHRs:</strong> Epic, Cerner, allscripts, athenahealth</li>
                    <li><strong>Standards:</strong> SMART on FHIR 2.0, FHIR R4</li>
                    <li><strong>Security:</strong> HIPAA compliant, enterprise-grade</li>
                </ul>
            </div>
        </body>
        </html>
        """)

# --- Documentation Route ---

@app.route('/docs')
@app.route('/documentation')
@app.route('/help')
def documentation():
    """
    Serves the comprehensive documentation page with detailed information about:
    - PRECISE-DAPT clinical evidence and validation
    - Scoring methodology and calculation details
    - Technical implementation and API documentation
    - EHR integration guidelines
    - Security and compliance information
    """
    try:
        return send_from_directory('.', 'docs.html')
    except FileNotFoundError:
        # Fallback to a basic documentation page
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PRECISE-DAPT Documentation</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }
                .header { text-align: center; background: #f8f9fa; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
                .section { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 25px; margin-bottom: 25px; }
                .score-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                .score-table th { background: #007bff; color: white; padding: 10px; }
                .score-table td { padding: 10px; border: 1px solid #ddd; }
                .risk-box { padding: 15px; margin: 10px 0; border-radius: 5px; color: white; text-align: center; }
                .low-risk { background: #28a745; }
                .moderate-risk { background: #ffc107; color: #333; }
                .high-risk { background: #dc3545; }
                .nav { text-align: center; margin-bottom: 30px; }
                .nav a { display: inline-block; margin: 5px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📚 PRECISE-DAPT Documentation</h1>
                <p>Comprehensive Guide to Bleeding Risk Assessment</p>
            </div>
            
            <div class="nav">
                <a href="/landing">← Back to Landing</a>
                <a href="/launch/cerner-sandbox">Try Demo</a>
                <a href="/">Launch App</a>
            </div>
            
            <div class="section">
                <h2>🏥 Clinical Overview</h2>
                <p>The PRECISE-DAPT score is a validated tool for assessing bleeding risk in patients on dual antiplatelet therapy (DAPT) following percutaneous coronary intervention (PCI).</p>
                
                <h3>Key Clinical Benefits:</h3>
                <ul>
                    <li><strong>Evidence-Based:</strong> Derived from 14,963 patients across 8 randomized trials</li>
                    <li><strong>Validated:</strong> C-statistic of 0.73 with excellent calibration</li>
                    <li><strong>Actionable:</strong> Guides DAPT duration decisions</li>
                    <li><strong>Practical:</strong> Uses readily available clinical parameters</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>🧮 Scoring Components</h2>
                <p>The PRECISE-DAPT score uses five clinical parameters:</p>
                
                <table class="score-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Scoring</th>
                            <th>Max Points</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Age</strong></td>
                            <td>&lt;65: 0pts, 65-74: 12pts, ≥75: 24pts</td>
                            <td>24</td>
                        </tr>
                        <tr>
                            <td><strong>Hemoglobin</strong></td>
                            <td>Normal: 0pts, Mild anemia: 2.5pts, Moderate: 5pts</td>
                            <td>5</td>
                        </tr>
                        <tr>
                            <td><strong>Creatinine Clearance</strong></td>
                            <td>≥60: 0pts, 30-59: 6pts, 15-29: 12pts, &lt;15: 18pts</td>
                            <td>18</td>
                        </tr>
                        <tr>
                            <td><strong>WBC Count</strong></td>
                            <td>&lt;11: 0pts, ≥11: 3pts</td>
                            <td>3</td>
                        </tr>
                        <tr>
                            <td><strong>Prior Bleeding</strong></td>
                            <td>No: 0pts, Yes: 6pts</td>
                            <td>6</td>
                        </tr>
                    </tbody>
                </table>
                
                <p><strong>Total Score Range:</strong> 0 - 56 points</p>
            </div>
            
            <div class="section">
                <h2>📊 Risk Stratification</h2>
                
                <div class="risk-box low-risk">
                    <strong>Low Risk (0-15 points)</strong><br>
                    1-year bleeding rate: 1.9%<br>
                    Recommendation: Standard DAPT (12 months)
                </div>
                
                <div class="risk-box moderate-risk">
                    <strong>Moderate Risk (16-24 points)</strong><br>
                    1-year bleeding rate: 3.7%<br>
                    Recommendation: Consider individual factors
                </div>
                
                <div class="risk-box high-risk">
                    <strong>High Risk (≥25 points)</strong><br>
                    1-year bleeding rate: 7.8%<br>
                    Recommendation: Consider shorter DAPT (3-6 months)
                </div>
            </div>
            
            <div class="section">
                <h2>⚡ Technical Implementation</h2>
                
                <h3>SMART on FHIR Integration</h3>
                <ul>
                    <li><strong>Standards Compliance:</strong> FHIR R4, SMART on FHIR 2.0</li>
                    <li><strong>Launch Sequence:</strong> Standard EHR-initiated launch</li>
                    <li><strong>Data Access:</strong> OAuth2 secured FHIR API calls</li>
                    <li><strong>Real-time Calculation:</strong> Immediate risk assessment</li>
                </ul>
                
                <h3>CDS Hooks Support</h3>
                <ul>
                    <li><strong>medication-prescribe:</strong> Alerts when prescribing DAPT</li>
                    <li><strong>patient-view:</strong> Risk information in patient summary</li>
                    <li><strong>Real-time Alerts:</strong> High-risk patient notifications</li>
                </ul>
                
                <h3>Security & Compliance</h3>
                <ul>
                    <li><strong>HIPAA Compliant:</strong> Secure data handling</li>
                    <li><strong>No Persistent Storage:</strong> Patient data not retained</li>
                    <li><strong>Audit Logging:</strong> Complete access trail</li>
                    <li><strong>Encrypted Transport:</strong> HTTPS only</li>
                </ul>
            </div>
            
            <div class="section">
                <h2>🔗 API Endpoints</h2>
                
                <h3>Risk Calculation</h3>
                <p><code>GET /api/calculate_risk</code></p>
                <p>Returns patient bleeding risk assessment with detailed component breakdown.</p>
                
                <h3>CDS Services Discovery</h3>
                <p><code>GET /cds-services</code></p>
                <p>Returns available CDS Hooks services for EHR integration.</p>
                
                <h3>DAPT Risk Alert</h3>
                <p><code>POST /cds-services/dapt_bleeding_risk_alert</code></p>
                <p>CDS Hook endpoint for medication prescribing workflow.</p>
            </div>
            
            <div class="section">
                <h2>📞 Support & Integration</h2>
                <p>For implementation support or clinical questions:</p>
                <ul>
                    <li><strong>Compatible EHRs:</strong> Epic, Cerner, allscripts, athenahealth</li>
                    <li><strong>Technical Requirements:</strong> SMART on FHIR enabled EHR</li>
                    <li><strong>Implementation Time:</strong> Typically 2-4 weeks</li>
                    <li><strong>Training:</strong> Comprehensive user training provided</li>
                </ul>
                
                <p><strong>Clinical Evidence:</strong> Costa F, et al. Lancet. 2017;389(10073):1025-1034.</p>
            </div>
        </body>
        </html>
        """)

# --- Logo Route ---

@app.route('/logo')
@app.route('/app_logo')
def app_logo():
    """
    Serves the application logo page showing the PRECISE-DAPT logo
    in various sizes and formats. Useful for:
    - Logo reference and brand guidelines
    - Downloading logo assets
    - Preview of the application branding
    """
    try:
        return send_from_directory('.', 'app_logo.html')
    except FileNotFoundError:
        # Fallback with basic logo information
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PRECISE-DAPT Logo</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; text-align: center; }
                .logo-container { background: #f8f9fa; padding: 30px; border-radius: 15px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>PRECISE-DAPT Logo</h1>
            <div class="logo-container">
                <svg width="128" height="128" viewBox="0 0 256 256">
                    <circle cx="128" cy="128" r="118" fill="#f0f9ff" stroke="#2563eb" stroke-width="6"/>
                    <path d="M 50 128 A 78 78 0 0 1 206 128" fill="none" stroke-width="14" stroke="url(#logoGrad)" stroke-linecap="round"/>
                    <circle cx="65" cy="145" r="6" fill="#10b981"/>
                    <circle cx="128" cy="55" r="6" fill="#f59e0b"/>
                    <circle cx="191" cy="145" r="6" fill="#ef4444"/>
                    <path d="M128 85 C118 75, 100 75, 100 92 C100 108, 128 135, 128 135 C128 135, 156 108, 156 92 C156 75, 138 75, 128 85 Z" fill="#dc2626"/>
                    <text x="128" y="215" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#1e40af">PRECISE-DAPT</text>
                    <defs>
                        <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" style="stop-color:#10b981"/>
                            <stop offset="50%" style="stop-color:#f59e0b"/>
                            <stop offset="100%" style="stop-color:#ef4444"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
            <p>Professional logo for the PRECISE-DAPT Bleeding Risk Calculator</p>
            <p><a href="/">← Back to App</a> | <a href="/landing">Landing Page</a></p>
        </body>
        </html>
        """)

# --- End of Logo Route ---

# --- Main Execution ---
if __name__ == '__main__':
    # This is used when running locally. When deploying, Gunicorn is used.
    app.run(host="127.0.0.1", port=8080, debug=True) 