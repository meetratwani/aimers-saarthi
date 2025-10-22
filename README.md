# Aimers Saarthi

An AI-powered automated grading system for CBSE Class answers with OCR capabilities, intelligent assessment, and email reporting.  

🌐 **Website:** [Visit Aimers Saarthi](https://aimers-cx0o.onrender.com)

## Features

- **OCR Text Extraction**: Upload answer sheets and extract handwritten/printed text using OCR.space API
- **AI-Powered Grading**: Automatic grading using Google Gemini AI based on CBSE marking schemes
- **Email Reports**: Send detailed grading reports via Gmail using Composio integration
- **Firebase Authentication**: Secure user authentication with Google Firebase
- **Results Management**: Save and track grading results with JSON storage
- **Modern UI**: Clean, responsive interface with real-time feedback

## Architecture

### Backend (Flask)
- **server.py** (Port 5000): Core grading engine with OCR and email functionality
- **app.py** (Port 4000): User authentication and session management

### Frontend
- Firebase Authentication
- Responsive HTML/CSS/JavaScript interface
- Real-time status updates

## Prerequisites

- Python 3.8+
- Firebase account with Admin SDK credentials
- Google Gemini API key
- Composio API key
- OCR.space API key

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jai-git4208/aimers-saarthi
cd cbse-auto-grader
```

### 2. Install Dependencies

```bash
pip install flask flask-cors firebase-admin composio composio-gemini google-genai pillow requests werkzeug
```

### 3. Configuration

#### Firebase Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Download Admin SDK credentials JSON
4. Place it as `aimers-62228-firebase-adminsdk-fbsvc-910a61401c.json` in root directory

#### API Keys Configuration

Edit `server.py` and update these values:

```python
# OCR.space API Key
OCR_SPACE_API_KEY = "your_ocr_space_api_key"

# Composio Configuration
COMPOSIO_API_KEY = "your_composio_api_key"
GEMINI_API_KEY = "your_gemini_api_key"
DEFAULT_USER_EMAIL = "your_email@gmail.com"
EXTERNAL_USER_ID = "your_unique_user_id"
AUTH_CONFIG_ID = "your_auth_config_id"
```

Edit `app.py`:

```python
app.secret_key = 'your-random-secret-key-here'
```

### 4. Create Required Directories

```bash
mkdir uploads results
```

## Usage

### Start the Servers

**Terminal 1 - Authentication Server:**
```bash
python app.py
```
Server runs on: `http://localhost:4000`

**Terminal 2 - Grading Server:**
```bash
python server.py
```
Server runs on: `http://localhost:5000`

### Gmail Connection Setup

Before sending emails, connect your Gmail account:

1. Visit: `http://localhost:5000/connect-gmail`
2. Authorize with your Google account
3. Grant Gmail permissions
4. Connection will be confirmed automatically

### API Endpoints

#### Authentication Server (Port 4000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page (redirects based on auth) |
| GET | `/login` | Login page |
| GET | `/signup` | Signup page |
| GET | `/dashboard` | User dashboard |
| POST | `/verify-token` | Verify Firebase ID token |
| POST | `/logout` | Logout user |
| GET | `/get-user-info` | Get current user info |

#### Grading Server (Port 5000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check & service status |
| GET | `/connect-gmail` | Initiate Gmail OAuth connection |
| GET | `/check-gmail-connection` | Check Gmail connection status |
| POST | `/extract-text` | Extract text from uploaded image |
| POST | `/submit-question` | Submit question details |
| POST | `/grade-answer` | Grade the submitted answer |
| POST | `/send-grading-email` | Send grading report via email |
| POST | `/full-grading-workflow` | Complete workflow (grade + email) |

### Workflow Example

#### 1. Extract Text from Answer Sheet

```bash
curl -X POST http://localhost:5000/extract-text \
  -F "image=@answer_sheet.jpg"
```

Response:
```json
{
  "success": true,
  "filename": "answer_sheet.jpg",
  "text": "Extracted text content...",
  "total_detections": 245
}
```

#### 2. Submit Question

```bash
curl -X POST http://localhost:5000/submit-question \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain photosynthesis process",
    "subject": "Biology",
    "max_marks": 5
  }'
```

#### 3. Complete Grading Workflow

```bash
curl -X POST http://localhost:5000/full-grading-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "user_email": "student@example.com"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Answer graded and email sent successfully",
  "grading": {
    "marks_awarded": 4,
    "max_marks": 5,
    "feedback": "Good explanation but missing chlorophyll details."
  },
  "email_sent": true,
  "email_sent_to": "student@example.com"
}
```

## Project Structure

```
cbse-auto-grader/
├── server.py                          # Main grading server
├── app.py                             # Authentication server
├── aimers-*-firebase-adminsdk.json   # Firebase credentials
├── uploads/                           # Uploaded answer sheets
├── results/                           # Grading results (JSON)
│   ├── answer.json                   # Current answer data
│   └── grading_result.json           # Grading output
├── templates/                         # HTML templates
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── answer.html
│   └── profile.html
├── static/                            # CSS, JS, images
└── README.md
```

## Configuration Details

### Supported Image Formats
- PNG, JPG, JPEG, WebP, BMP, GIF, TIFF, PDF
- Max file size: 16MB

### OCR Settings
- Engine: OCR.space API (Engine 2)
- Language: English (configurable)
- Timeout: 60 seconds
- Auto-retry: 3 attempts

### AI Grading
- Model: Google Gemini 2.0 Flash
- Marking scheme: CBSE Class 10 standards
- Output: JSON format with marks and feedback

## Security Notes

**Important Security Measures:**

1. **Never commit API keys** to version control
2. Use environment variables for production:
   ```python
   import os
   GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
   ```
3. Change `app.secret_key` to a random secure value
4. Enable CORS only for trusted domains in production
5. Store Firebase credentials securely

## Troubleshooting

### Gmail Connection Issues
- Ensure Composio Auth Config is properly set up
- Check that EXTERNAL_USER_ID matches your Composio account
- Verify Gmail API scopes in Google Cloud Console

### OCR Failures
- Check image quality and size (max 16MB)
- Verify OCR.space API key is active
- Ensure internet connectivity for API calls

### Firebase Authentication Errors
- Verify Firebase credentials file exists
- Check Firebase project settings
- Ensure web app is registered in Firebase console

## Monitoring

Check service health:
```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "ocr": "OCR.space",
    "grading": "Gemini AI",
    "email": "Composio + Gmail (connected)"
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- **OCR.space** for text extraction API
- **Google Gemini** for AI grading capabilities
- **Composio** for Gmail integration
- **Firebase** for authentication services

## Support

For issues or questions:
- Open an issue on GitHub
- Contact: meetgaming43@gmail.com

---

**Made with care for CBSE Students & Teachers**
