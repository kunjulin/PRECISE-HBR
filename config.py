import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    
    # Determine session directory based on environment
    # App Engine has read-only filesystem except for /tmp
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Running on Google App Engine - use secure temp directory
        import tempfile
        SESSION_FILE_DIR = os.path.join(tempfile.gettempdir(), 'flask_session')
    else:
        # Running locally or on other platforms
        SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'flask_session')

    # SMART on FHIR configuration
    CLIENT_ID = os.environ.get('SMART_CLIENT_ID')
    REDIRECT_URI = os.environ.get('SMART_REDIRECT_URI')
    SCOPES = "launch patient/Patient.read patient/Observation.read patient/Condition.read patient/MedicationRequest.read patient/Procedure.read fhirUser openid profile online_access user/Patient.read user/Observation.read user/Condition.read user/MedicationRequest.read user/Procedure.read"

    # Cerner Sandbox Configuration (as a fallback or for specific testing)
    CERNER_SANDBOX_CONFIG = {
        'fhir_base': 'https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d',
        'authorization_endpoint': 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v2/personas/provider/authorize',
        'token_endpoint': 'https://authorization.cerner.com/tenants/ec2458f2-1e24-41c8-b71b-0e701af7583d/protocols/oauth2/profiles/smart-v2/token',
        'tenant_id': 'ec2458f2-1e24-41c8-b71b-0e701af7583d'
    }

    @staticmethod
    def init_app(app):
        # Pre-flight checks for essential configuration
        if not Config.SECRET_KEY:
            raise ValueError("FATAL: FLASK_SECRET_KEY must be set in the environment.")
        
        if not Config.CLIENT_ID or not Config.REDIRECT_URI:
            raise ValueError(
                "FATAL: SMART_CLIENT_ID and SMART_REDIRECT_URI must be set in the environment.")

        # Clean up REDIRECT_URI
        if Config.REDIRECT_URI and '#' in Config.REDIRECT_URI:
            Config.REDIRECT_URI = Config.REDIRECT_URI.split('#')[0].strip()

        # R-02 Risk Mitigation: Ensure session directory exists with secure permissions
        if not os.path.exists(Config.SESSION_FILE_DIR):
            try:
                os.makedirs(Config.SESSION_FILE_DIR, mode=0o700)  # Owner read/write/execute only
                app.logger.info(f"Created secure session directory: {Config.SESSION_FILE_DIR}")
            except OSError as e:
                app.logger.warning(
                    f"Could not create session directory: {e}. Using default session handling.")
        else:
            # Ensure existing directory has secure permissions
            try:
                os.chmod(Config.SESSION_FILE_DIR, 0o700)
                app.logger.debug(f"Set secure permissions on session directory: {Config.SESSION_FILE_DIR}")
            except OSError as e:
                app.logger.warning(f"Could not set secure permissions on session directory: {e}")
