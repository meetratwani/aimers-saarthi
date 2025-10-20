from flask import Flask, request, jsonify, send_from_directory, render_template_string, redirect
from flask_cors import CORS
from composio import Composio
from composio_gemini import GeminiProvider
from google import genai
from google.genai import types
import io
import os
import json
import re
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
CORS(app)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'gif', 'tiff', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# === OCR.SPACE CONFIG ===
OCR_SPACE_API_KEY = "YOUR-API-KEY"
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

# === GRADING SYSTEM CONFIG ===
COMPOSIO_API_KEY = "API-KEY-FROM-COMPOSIO"
GEMINI_API_KEY = "API-KEY-FROM-GOOGLE-GEMINI"
DEFAULT_USER_EMAIL = "YOUR-EMAIL@gmail.com"
EXTERNAL_USER_ID = "USER-ID-1234"
AUTH_CONFIG_ID = "YOUR-AUTH-CONFIG-ID"

# Initialize Composio with Gemini Provider
composio = Composio(api_key=COMPOSIO_API_KEY, provider=GeminiProvider())
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

print("✓ OCR.space and Composio configuration loaded")

# Store pending connection requests in memory
pending_connections = {}

# === OAUTH CONNECTION PAGES ===
OAUTH_SETUP_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Connect Gmail - CBSE Grader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 20px;
            font-size: 2em;
        }
        .icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            background: #f0f4ff;
            color: #667eea;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📧</div>
        <h1>Redirecting to Gmail</h1>
        <div class="spinner"></div>
        <p>Please wait while we redirect you to Google for authorization...</p>
        
        <div class="status">
            ⏳ Redirecting...
        </div>
        
        <p style="margin-top: 30px; font-size: 0.9em; color: #999;">
            If you're not redirected automatically, <a href="{{ oauth_url }}" style="color: #667eea;">click here</a>
        </p>
    </div>
    
    <script>
        // Auto-redirect to OAuth URL
        setTimeout(() => {
            window.location.href = '{{ oauth_url }}';
        }, 1000);
    </script>
</body>
</html>
"""

OAUTH_SUCCESS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Gmail Connected - CBSE Grader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            color: #2e7d32;
            margin-bottom: 20px;
            font-size: 2em;
        }
        .icon {
            font-size: 5em;
            margin-bottom: 20px;
            animation: bounce 1s ease infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .info-box {
            background: #e8f5e9;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            text-align: left;
        }
        .info-box strong {
            color: #2e7d32;
        }
        .back-btn {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            transition: transform 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .back-btn:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✅</div>
        <h1>Gmail Connected Successfully!</h1>
        <p>Your Gmail account has been connected and you can now send grading reports via email.</p>
        
        <div class="info-box">
            <p><strong>Connection ID:</strong> {{ connection_id }}</p>
            <p><strong>User ID:</strong> {{ user_id }}</p>
            <p><strong>Status:</strong> Active ✓</p>
        </div>
        
        <p>This window will close automatically...</p>
    </div>
    
    <script>
        console.log('Gmail connected successfully, notifying parent window...');
        
        // Notify parent window immediately
        if (window.opener) {
            window.opener.postMessage('gmail_connected', '*');
            console.log('Message sent to parent window');
        }
        
        // Auto-close window after a delay
        setTimeout(() => {
            console.log('Attempting to close window...');
            if (window.opener) {
                window.close();
            } else {
                // If not in popup, redirect to home
                console.log('Not in popup, redirecting to home...');
                window.location.href = '/';
            }
        }, 3000);
    </script>
</body>
</html>
"""

OAUTH_ERROR_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Connection Failed - CBSE Grader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            color: #d32f2f;
            margin-bottom: 20px;
            font-size: 2em;
        }
        .icon {
            font-size: 5em;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .error-box {
            background: #ffebee;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            color: #c62828;
        }
        .retry-btn {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 50px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Connection Failed</h1>
        <p>We couldn't connect your Gmail account.</p>
        
        <div class="error-box">
            <p><strong>Error:</strong> {{ error_message }}</p>
        </div>
        
        <p>Please try again or contact support if the issue persists.</p>
        
        <a href="/connect-gmail" class="retry-btn">🔄 Try Again</a>
    </div>
</body>
</html>
"""

# === HELPER FUNCTIONS ===
def is_gmail_connected():
    """Check if Gmail is connected for the user"""
    try:
        # Get connected accounts - returns ConnectedAccountListResponse object
        result = composio.connected_accounts.list()
        
        # Access the items directly from the response object
        connections = result.items if hasattr(result, 'items') else []
        
        print(f"🔍 Checking connections... Found {len(connections)} total connections")
        
        # Filter for Gmail connections that are active
        for conn in connections:
            # Try different attribute names that might contain the integration name
            integration = None
            if hasattr(conn, 'integration_name'):
                integration = conn.integration_name
            elif hasattr(conn, 'integrationName'):
                integration = conn.integrationName
            elif hasattr(conn, 'appName'):
                integration = conn.appName
            elif hasattr(conn, 'app_name'):
                integration = conn.app_name
            
            status = conn.status if hasattr(conn, 'status') else 'Unknown'
            conn_id = conn.id if hasattr(conn, 'id') else 'Unknown'
            
            # Debug: print all attributes of the connection object
            print(f"  - Connection ID: {conn_id} | Status: {status} | Integration: {integration}")
            print(f"    Available attributes: {dir(conn)}")
            
            # Check if it's Gmail and ACTIVE
            if integration and integration.upper() == "GMAIL" and status == "ACTIVE":
                print(f"✅ Found active Gmail connection: {conn_id}")
                return True
            
            # Also check if any ACTIVE connection exists (might be Gmail)
            if status == "ACTIVE":
                print(f"⚠️  Found ACTIVE connection but integration name unclear: {conn_id}")
                # Let's assume the first ACTIVE connection might be Gmail
                print(f"✅ Assuming ACTIVE connection {conn_id} is Gmail")
                return True
        
        print("❌ No active Gmail connection found")
        return False
    except Exception as e:
        print(f"❌ Error checking connection: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_result_to_json(result_data, filename):
    """Save OCR result to JSON file"""
    base_name = os.path.splitext(filename)[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{base_name}_{timestamp}.json"
    json_path = os.path.join(app.config['RESULTS_FOLDER'], json_filename)
    
    result_data['metadata'] = {
        'source_image': filename,
        'processed_at': datetime.now().isoformat(),
        'saved_at': json_path
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Result saved to: {json_path}")
    return json_path

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ocr_space_file(filename, overlay=False, api_key=OCR_SPACE_API_KEY, language='eng', max_retries=3):
    """OCR.space API request with local file"""
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
        'OCREngine': 2,
    }
    
    for attempt in range(max_retries):
        try:
            print(f"📤 OCR attempt {attempt + 1}/{max_retries}...")
            with open(filename, 'rb') as f:
                r = requests.post(
                    OCR_SPACE_URL,
                    files={filename: f},
                    data=payload,
                    timeout=60  # Increased from 30 to 60 seconds
                )
            r.raise_for_status()
            print(f"✅ OCR successful on attempt {attempt + 1}")
            return r.json()
        except requests.exceptions.Timeout as e:
            print(f"⏱️ OCR timeout on attempt {attempt + 1}/{max_retries}")
            if attempt == max_retries - 1:
                print(f"❌ OCR failed after {max_retries} attempts")
                return {'IsErroredOnProcessing': True, 'ErrorMessage': [f'Request timed out after {max_retries} attempts. Please try with a smaller image.']}
            print(f"🔄 Retrying...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"❌ OCR.space API error: {e}")
            return {'IsErroredOnProcessing': True, 'ErrorMessage': [str(e)]}
        except Exception as e:
            print(f"❌ Error reading file or parsing response: {e}")
            return {'IsErroredOnProcessing': True, 'ErrorMessage': [str(e)]}

def parse_ocr_result(ocr_result):
    """Parse OCR.space result into standardized format"""
    if not ocr_result.get('IsErroredOnProcessing', True):
        parsed_results = ocr_result.get('ParsedResults', [])
        if parsed_results:
            full_text = parsed_results[0].get('ParsedText', '')
            
            detailed_results = []
            text_overlay = parsed_results[0].get('TextOverlay', {})
            lines = text_overlay.get('Lines', [])
            
            for line in lines:
                line_text = line.get('LineText', '')
                words = line.get('Words', [])
                
                for word in words:
                    word_text = word.get('WordText', '')
                    left = word.get('Left', 0)
                    top = word.get('Top', 0)
                    height = word.get('Height', 0)
                    width = word.get('Width', 0)
                    
                    bbox = [
                        {"x": left, "y": top},
                        {"x": left + width, "y": top},
                        {"x": left + width, "y": top + height},
                        {"x": left, "y": top + height}
                    ]
                    
                    detailed_results.append({
                        'text': word_text,
                        'bbox': bbox
                    })
            
            return full_text, detailed_results
    
    return "", []

def safe_json_parse(response_text):
    """Safely parse JSON from Gemini response"""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Gemini response not in JSON format:\n" + response_text)

# === EMAIL SENDING ENDPOINT ===
def send_email_via_composio(recipient_email, subject, body):
    """Send email using Composio Gmail integration with manual function calling"""
    try:
        print(f"📧 Preparing to send email to: {recipient_email}")
        
        # Check if Gmail is connected
        if not is_gmail_connected():
            return {
                'success': False,
                'error': 'Gmail not connected',
                'action_required': 'connect_gmail',
                'connect_url': f"{request.url_root}connect-gmail"
            }
        
        # Get only GMAIL_SEND_EMAIL tool (not drafts)
        print(f"🔧 Getting GMAIL_SEND_EMAIL tool for user: {EXTERNAL_USER_ID}")
        tools = composio.tools.get(user_id=EXTERNAL_USER_ID, tools=["GMAIL_SEND_EMAIL"])
        print(f"✅ Tools retrieved: {len(tools)} tools available")
        
        # Create config for Gemini WITHOUT automatic function calling
        config = types.GenerateContentConfig(tools=tools)
        
        # Create chat instance
        print(f"💬 Creating chat instance...")
        chat = gemini_client.chats.create(model="gemini-2.0-flash", config=config)
        
        # Send message to get function call suggestion
        prompt = f"""Send (do not draft) an email using Gmail to {recipient_email} with subject '{subject}' and body '{body}'"""
        
        print(f"🤖 Sending prompt to Gemini...")
        response = chat.send_message(prompt)
        
        print(f"📥 Response received")
        print(f"[!] Response candidates: {response.candidates}")
        
        # Check if there are function calls in the response
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            print(f"[!] Candidate content parts: {candidate.content.parts}")
            
            # Look for function calls
            email_sent = False
            for part in candidate.content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    print(f"[!] Function call detected: {function_call.name}")
                    print(f"[!] Function args: {function_call.args}")
                    
                    # Execute the function call using composio.tools.execute()
                    try:
                        result = composio.tools.execute(
                            slug=function_call.name,
                            arguments=function_call.args,
                            user_id=EXTERNAL_USER_ID
                        )
                        print(f"[!] ✅ Tool executed successfully!")
                        print(f"[!] Result: {result}")
                        email_sent = True
                        
                        return {
                            'success': True,
                            'message': 'Email sent successfully',
                            'function_called': function_call.name,
                            'result': str(result)
                        }
                    except Exception as e:
                        print(f"[!] ❌ Error executing tool: {e}")
                        import traceback
                        traceback.print_exc()
                        return {
                            'success': False,
                            'error': f'Failed to execute email tool: {str(e)}'
                        }
                elif hasattr(part, 'text'):
                    print(f"[!] Text response: {part.text}")
            
            if not email_sent:
                return {
                    'success': False,
                    'error': 'No function call detected in Gemini response',
                    'response': response.text if hasattr(response, 'text') else str(response)
                }
        else:
            return {
                'success': False,
                'error': 'No response candidates from Gemini',
                'response': str(response)
            }
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e)
        }
    
            
# === OAUTH ENDPOINTS ===
@app.route('/connect-gmail', methods=['GET'])
def connect_gmail():
    """Initiate Gmail OAuth connection"""
    try:
        print("🔗 Initiating Gmail OAuth connection...")
        
        # Check if already connected
        if is_gmail_connected():
            print("✅ Already connected to Gmail")
            return render_template_string(OAUTH_SUCCESS_PAGE, 
                connection_id="Already Connected",
                user_id=EXTERNAL_USER_ID
            )
        
        # Create connection request
        print(f"📍 Creating connection for user: {EXTERNAL_USER_ID}")
        
        connection_request = composio.connected_accounts.link(
            user_id=EXTERNAL_USER_ID,
            auth_config_id=AUTH_CONFIG_ID
        )
        
        # Store the connection request
        pending_connections[EXTERNAL_USER_ID] = connection_request
        
        oauth_url = connection_request.redirect_url
        print(f"📝 OAuth URL generated: {oauth_url}")
        print(f"🔑 Connection request stored for user: {EXTERNAL_USER_ID}")
        
        return render_template_string(OAUTH_SETUP_PAGE, oauth_url=oauth_url)
    
    except Exception as e:
        print(f"❌ Error initiating OAuth: {e}")
        import traceback
        traceback.print_exc()
        return render_template_string(OAUTH_ERROR_PAGE, error_message=str(e)), 500

@app.route('/oauth-callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback - This might not be called directly by Composio"""
    try:
        print("✅ OAuth callback endpoint hit")
        print(f"📦 Query params: {request.args}")
        
        # Check if connection was successful by verifying active connections
        if is_gmail_connected():
            result = composio.connected_accounts.list()
            connections = result.items if hasattr(result, 'items') else []
            
            gmail_conn = None
            for c in connections:
                if hasattr(c, 'integration_name') and c.integration_name == "GMAIL" and c.status == "ACTIVE":
                    gmail_conn = c
                    break
            
            if gmail_conn:
                print(f"✅ Gmail connection verified: {gmail_conn.id}")
                return render_template_string(OAUTH_SUCCESS_PAGE,
                    connection_id=gmail_conn.id,
                    user_id=EXTERNAL_USER_ID
                )
        
        # If not connected yet, show error
        return render_template_string(OAUTH_ERROR_PAGE, 
            error_message="Connection not found. Please try again or contact support."
        ), 400
    
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return render_template_string(OAUTH_ERROR_PAGE, error_message=str(e)), 500

@app.route('/wait-for-connection/<user_id>', methods=['GET'])
def wait_for_connection_endpoint(user_id):
    """Wait for OAuth connection to complete - called via AJAX"""
    try:
        print(f"⏳ Waiting for connection for user: {user_id}")
        
        # Get the pending connection request
        connection_request = pending_connections.get(user_id)
        
        if not connection_request:
            return jsonify({
                'success': False,
                'error': 'No pending connection request found'
            }), 404
        
        # Wait for connection with timeout (this blocks until OAuth completes)
        print("⏳ Blocking until OAuth completes...")
        connected_account = connection_request.wait_for_connection(timeout=120)
        
        print(f"✅ Connection established successfully! ID: {connected_account.id}")
        
        # Remove from pending
        pending_connections.pop(user_id, None)
        
        return jsonify({
            'success': True,
            'connected': True,
            'connection_id': connected_account.id,
            'integration': connected_account.integration_name if hasattr(connected_account, 'integration_name') else 'GMAIL',
            'status': connected_account.status if hasattr(connected_account, 'status') else 'ACTIVE'
        }), 200
        
    except Exception as e:
        print(f"❌ Error waiting for connection: {e}")
        import traceback
        traceback.print_exc()
        
        # Remove from pending on error
        pending_connections.pop(user_id, None)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'connected': False
        }), 500

@app.route('/check-gmail-connection', methods=['GET'])
def check_gmail_connection():
    """Check if Gmail is connected for the user"""
    try:
        print(f"🔍 Checking Gmail connection for user: {EXTERNAL_USER_ID}")
        
        # Get connected accounts
        result = composio.connected_accounts.list()
        connections = result.items if hasattr(result, 'items') else []
        
        print(f"📊 Total connections found: {len(connections)}")
        
        gmail_connections = []
        has_active_connection = False
        
        for conn in connections:
            # Try to get integration name from various possible attributes
            integration = 'Unknown'
            if hasattr(conn, 'integration_name'):
                integration = conn.integration_name
            elif hasattr(conn, 'integrationName'):
                integration = conn.integrationName
            elif hasattr(conn, 'appName'):
                integration = conn.appName
            elif hasattr(conn, 'app_name'):
                integration = conn.app_name
            
            conn_info = {
                'id': conn.id if hasattr(conn, 'id') else 'Unknown',
                'integration': integration,
                'status': conn.status if hasattr(conn, 'status') else 'Unknown',
                'all_attributes': {k: str(v) for k, v in conn.__dict__.items() if not k.startswith('_')}
            }
            print(f"  Connection: {conn_info}")
            
            # Check if ACTIVE (regardless of integration name being detected)
            if conn_info['status'] == 'ACTIVE':
                has_active_connection = True
                gmail_connections.append(conn_info)
        
        # Consider it connected if we have any ACTIVE connection
        is_connected = has_active_connection
        
        print(f"✅ Gmail connected: {is_connected}")
        
        return jsonify({
            'success': True,
            'gmail_connected': is_connected,
            'connections': gmail_connections,
            'all_connections_count': len(connections),
            'user_id': EXTERNAL_USER_ID,
            'connect_url': f"{request.url_root}connect-gmail" if not is_connected else None,
            'message': 'Gmail is connected ✓' if is_connected else 'Gmail not connected. Visit /connect-gmail to set up.'
        }), 200
    
    except Exception as e:
        print(f"❌ Error checking Gmail connection: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'gmail_connected': False
        }), 500

# === EXISTING ENDPOINTS ===
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    gmail_status = 'connected' if is_gmail_connected() else 'not connected'
    
    return jsonify({
        'status': 'healthy',
        'message': 'CBSE Grading & OCR server is running',
        'services': {
            'ocr': 'OCR.space',
            'grading': 'Gemini AI',
            'email': f'Composio + Gmail ({gmail_status})'
        },
        'gmail_setup_url': f"{request.url_root}connect-gmail" if gmail_status == 'not connected' else None
    }), 200

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded images as public URLs"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/extract-text', methods=['POST'])
def extract_text():
    """Extract text from uploaded image using OCR.space"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file provided',
                'message': 'Please upload an image file with key "image"'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type',
                'message': f'Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"Image saved: {filepath}")
        
        ocr_result = ocr_space_file(filepath, overlay=True)
        
        if not isinstance(ocr_result, dict):
            return jsonify({
                'error': 'OCR processing failed',
                'message': f'Invalid OCR response: {str(ocr_result)}'
            }), 500
        
        if ocr_result.get('IsErroredOnProcessing', True):
            error_messages = ocr_result.get('ErrorMessage', ['Unknown error'])
            error_message = error_messages[0] if isinstance(error_messages, list) else str(error_messages)
            return jsonify({
                'error': 'OCR processing failed',
                'message': error_message
            }), 500
        
        full_text, detailed_results = parse_ocr_result(ocr_result)
        
        public_url = f"{request.url_root}uploads/{filename}"
        
        result = {
            'success': True,
            'filename': filename,
            'public_url': public_url,
            'text': full_text,
            'detailed_results': detailed_results,
            'total_detections': len(detailed_results)
        }
        
        json_path = save_result_to_json(result, filename)
        result['json_saved_at'] = json_path
        
        # Save to answer.json for grading workflow
        answer_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'answer.json')
        
        existing_data = {}
        if os.path.exists(answer_json_path):
            try:
                with open(answer_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
        
        existing_data['text'] = full_text
        existing_data['source_image'] = filename
        existing_data['source_url'] = public_url
        existing_data['processed_at'] = datetime.now().isoformat()
        
        with open(answer_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Text also saved to answer.json for grading workflow")
        result['answer_json_saved_at'] = answer_json_path
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({
            'error': 'Processing failed',
            'message': str(e)
        }), 500

@app.route('/submit-question', methods=['POST'])
def submit_question():
    """Submit a question and save it to the answer.json file"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'error': 'No question provided',
                'message': 'Please provide a question in JSON'
            }), 400
        
        question = data['question']
        subject = data.get('subject', 'Unknown')
        max_marks = data.get('max_marks', 10)
        
        answer_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'answer.json')
        
        existing_data = {}
        if os.path.exists(answer_json_path):
            try:
                with open(answer_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
        
        existing_data['question'] = question
        existing_data['subject'] = subject
        existing_data['max_marks'] = max_marks
        existing_data['question_submitted_at'] = datetime.now().isoformat()
        
        with open(answer_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Question saved to: {answer_json_path}")
        
        return jsonify({
            'success': True,
            'message': 'Question saved successfully',
            'saved_at': answer_json_path,
            'data': {
                'question': question,
                'subject': subject,
                'max_marks': max_marks
            }
        }), 200
    
    except Exception as e:
        print(f"Error saving question: {str(e)}")
        return jsonify({
            'error': 'Failed to save question',
            'message': str(e)
        }), 500

@app.route('/grade-answer', methods=['POST'])
def grade_answer():
    """Grade the answer using Gemini AI"""
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email', DEFAULT_USER_EMAIL)
        
        answer_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'answer.json')
        
        if not os.path.exists(answer_json_path):
            return jsonify({
                'error': 'answer.json not found',
                'message': 'Please submit a question and extract text first'
            }), 404
        
        with open(answer_json_path, 'r') as f:
            answer_data = json.load(f)
        
        question = answer_data.get('question', 'No question provided')
        answer = answer_data.get('text', 'No answer provided')
        subject = answer_data.get('subject', 'Unknown')
        max_marks = answer_data.get('max_marks', 10)
        
        grading_prompt = f"""
You are an experienced CBSE teacher.
Grade the following student's answer according to the official CBSE marking scheme for class 10.

Question: {question}
Maximum Marks: {max_marks}
Answer: {answer}

Return ONLY valid JSON, no explanations, no extra text.
Example output:
{{"marks_awarded": 5, "max_marks": {max_marks}, "feedback": "Good structure but lacks examples."}}
"""
        
        grade_response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=grading_prompt
        )
        
        graded = safe_json_parse(grade_response.text)
        print(f"Graded: {graded}")
        
        grading_result = {
            'question': question,
            'answer': answer,
            'subject': subject,
            'grading': graded,
            'graded_at': datetime.now().isoformat()
        }
        
        grading_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'grading_result.json')
        with open(grading_json_path, 'w', encoding='utf-8') as f:
            json.dump(grading_result, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'grading': graded,
            'subject': subject,
            'result_saved_at': grading_json_path
        }), 200
    
    except Exception as e:
        print(f"Error grading answer: {str(e)}")
        return jsonify({
            'error': 'Grading failed',
            'message': str(e)
        }), 500

@app.route('/send-grading-email', methods=['POST'])
def send_grading_email():
    """Send grading results via email using Composio"""
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email', DEFAULT_USER_EMAIL)
        
        if not user_email or user_email == 'noemail@example.com':
            return jsonify({
                'error': 'Valid email required',
                'message': 'Please provide a valid email address'
            }), 400
        
        grading_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'grading_result.json')
        
        if not os.path.exists(grading_json_path):
            return jsonify({
                'error': 'grading_result.json not found',
                'message': 'Please grade the answer using /grade-answer first'
            }), 404
        
        with open(grading_json_path, 'r') as f:
            grading_data = json.load(f)
        
        graded = grading_data['grading']
        subject = grading_data.get('subject', 'Unknown')
        question = grading_data.get('question', 'N/A')
        
        # Prepare email content
        email_subject = f'CBSE Grading Report - {subject}'
        email_body = f"""Hi there,

Your answer has been graded by our AI system. Here are your results:

📚 Subject: {subject}
❓ Question: {question[:100]}...

📊 RESULTS:
═══════════════════════════════
Marks Awarded: {graded['marks_awarded']} / {graded['max_marks']}
Percentage: {round((graded['marks_awarded'] / graded['max_marks']) * 100)}%

📝 FEEDBACK:
{graded['feedback']}

═══════════════════════════════

Keep up the good work! 🌟

—
Automated CBSE Grader
Powered by Composio x Gemini AI
"""
        
        # Send email using Composio
        print(f"📧 Attempting to send email to: {user_email}")
        result = send_email_via_composio(user_email, email_subject, email_body)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Grading report sent successfully',
                'recipient': user_email,
                'subject': subject,
                'grading': graded
            }), 200
        elif result.get('action_required') == 'connect_gmail':
            return jsonify({
                'success': False,
                'error': 'Gmail not connected',
                'message': 'Please connect your Gmail account first',
                'connect_url': result.get('connect_url'),
                'action_required': 'connect_gmail'
            }), 403
        else:
            return jsonify({
                'error': 'Email sending failed',
                'message': result.get('error', 'Unknown error')
            }), 500
    
    except Exception as e:
        print(f"❌ Error in send_grading_email: {str(e)}")
        return jsonify({
            'error': 'Email sending failed',
            'message': str(e)
        }), 500

@app.route('/full-grading-workflow', methods=['POST'])
def full_grading_workflow():
    """Complete grading workflow: grade answer and send email in one call"""
    try:
        data = request.get_json() or {}
        user_email = data.get('user_email', DEFAULT_USER_EMAIL)
        
        # Check Gmail connection first
        if not is_gmail_connected():
            return jsonify({
                'success': False,
                'error': 'Gmail not connected',
                'message': 'Please connect your Gmail account first',
                'connect_url': f"{request.url_root}connect-gmail",
                'action_required': 'connect_gmail'
            }), 403
        
        # Step 1: Grade the answer
        answer_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'answer.json')
        
        if not os.path.exists(answer_json_path):
            return jsonify({
                'error': 'answer.json not found',
                'message': 'Please submit a question and extract text first'
            }), 404
        
        with open(answer_json_path, 'r') as f:
            answer_data = json.load(f)
        
        question = answer_data.get('question', 'No question provided')
        answer = answer_data.get('text', 'No answer provided')
        subject = answer_data.get('subject', 'Unknown')
        max_marks = answer_data.get('max_marks', 10)
        
        grading_prompt = f"""
You are an experienced CBSE teacher.
Grade the following student's answer according to the official CBSE marking scheme for class 10.

Question: {question}
Maximum Marks: {max_marks}
Answer: {answer}

Return ONLY valid JSON, no explanations, no extra text.
Example output:
{{"marks_awarded": 5, "max_marks": {max_marks}, "feedback": "Good structure but lacks examples."}}
"""
        
        grade_response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=grading_prompt
        )
        
        graded = safe_json_parse(grade_response.text)
        print(f"Graded: {graded}")
        
        grading_result = {
            'question': question,
            'answer': answer,
            'subject': subject,
            'grading': graded,
            'graded_at': datetime.now().isoformat()
        }
        
        grading_json_path = os.path.join(app.config['RESULTS_FOLDER'], 'grading_result.json')
        with open(grading_json_path, 'w', encoding='utf-8') as f:
            json.dump(grading_result, f, indent=2, ensure_ascii=False)
        
        # Step 2: Send email
        email_subject = f'CBSE Grading Report - {subject}'
        email_body = f"""Hi there,

Your answer has been graded by our AI system. Here are your results:

📚 Subject: {subject}
❓ Question: {question[:100]}...

📊 RESULTS:
═══════════════════════════════
Marks Awarded: {graded['marks_awarded']} / {graded['max_marks']}
Percentage: {round((graded['marks_awarded'] / graded['max_marks']) * 100)}%

📝 FEEDBACK:
{graded['feedback']}

═══════════════════════════════

Keep up the good work! 🌟

—
Automated CBSE Grader
Powered by Composio x Gemini AI
"""
        
        email_result = send_email_via_composio(user_email, email_subject, email_body)
        
        if not email_result['success']:
            return jsonify({
                'success': False,
                'grading': graded,
                'grading_saved': True,
                'email_sent': False,
                'error': email_result.get('error'),
                'message': 'Answer graded successfully but email sending failed'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Answer graded and email sent successfully',
            'grading': graded,
            'email_sent': True,
            'email_sent_to': user_email,
            'subject': subject,
            'results_saved_at': grading_json_path
        }), 200
    
    except Exception as e:
        print(f"Error in workflow: {str(e)}")
        return jsonify({
            'error': 'Workflow failed',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 CBSE Grading & OCR Server Starting...")
    print("="*70)
    print(f"User ID: {EXTERNAL_USER_ID}")
    print(f"Gmail Connected: {'✅ Yes' if is_gmail_connected() else '❌ No - Visit http://localhost:5000/connect-gmail'}")
    print("\n📋 Endpoints available:")
    print("  GET  /health                    - Health check")
    print("  GET  /connect-gmail             - Connect Gmail account (OAuth)")
    print("  GET  /check-gmail-connection    - Check Gmail connection status")
    print("  POST /extract-text              - Extract text from uploaded image")
    print("  POST /submit-question           - Submit question with subject & max_marks")
    print("  POST /grade-answer              - Grade answer using Gemini AI")
    print("  POST /send-grading-email        - Send grading report via email")
    print("  POST /full-grading-workflow     - Complete workflow (grade + email)")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)