from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import firebase_admin
from firebase_admin import credentials, auth
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Initialize Firebase Admin SDK
cred = credentials.Certificate('your-json-key-to-firebase-8238348.json')
firebase_admin.initialize_app(cred)
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

@app.route('/answer')
def answer():
    return render_template('answer.html')

@app.route('/upload')
def profile():
    return render_template('upload.html')

@app.route('/profile')
def upload():
    return render_template('profile.html')

@app.route('/signup')
def signup_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/test')
def test():
    if 'user_id' not in session:
        return redirect(url_for('dashboard'))
    return render_template('test.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        id_token = request.json.get('idToken')
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        # Store user info in session
        session['user_id'] = uid
        session['user_email'] = decoded_token.get('email')
        session['user_name'] = decoded_token.get('name', decoded_token.get('email').split('@')[0])
        
        return jsonify({
            'status': 'success',
            'message': 'Token verified successfully',
            'uid': uid
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out'}), 200

@app.route('/get-user-info', methods=['GET'])
def get_user_info():
    if 'user_id' in session:
        return jsonify({
            'status': 'success',
            'user_id': session['user_id'],
            'user_email': session.get('user_email', ''),
            'user_name': session.get('user_name', '')
        }), 200
    else:
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized'
        }), 401

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=4000, debug=True)