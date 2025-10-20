import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signInWithPopup, 
    GoogleAuthProvider, 
    onAuthStateChanged, 
    signOut 
} from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// Your Firebase configuration
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "aimers-62228.firebaseapp.com",
    projectId: "aimers-62228",
    storageBucket: "aimers-62228.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// Get DOM elements
const signInBtn = document.getElementById('signInBtn');
const googleSignInBtn = document.getElementById('googleSignInBtn');
const signOutBtn = document.getElementById('signOutBtn');
const signUpBtn = document.getElementById('signUpBtn');
const showSignUp = document.getElementById('showSignUp');
const showSignIn = document.getElementById('showSignIn');
const whenSignedIn = document.getElementById('whenSignedIn');
const whenSignedOut = document.getElementById('whenSignedOut');
const signUpSection = document.getElementById('signUpSection');
const errorMessage = document.getElementById('errorMessage');

// Toggle between Sign In and Sign Up
showSignUp.addEventListener('click', () => {
    whenSignedOut.style.display = 'none';
    signUpSection.style.display = 'block';
    errorMessage.textContent = '';
});

showSignIn.addEventListener('click', () => {
    signUpSection.style.display = 'none';
    whenSignedOut.style.display = 'block';
    errorMessage.textContent = '';
});

// Email/Password Sign In
signInBtn.addEventListener('click', () => {
    const email = document.getElementById('emailInput').value;
    const password = document.getElementById('passwordInput').value;

    signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            console.log('User signed in:', userCredential.user);
            errorMessage.textContent = '';
            sendTokenToFlask(userCredential.user);
        })
        .catch((error) => {
            errorMessage.textContent = error.message;
            console.error('Error:', error);
        });
});

// Email/Password Sign Up
signUpBtn.addEventListener('click', () => {
    const email = document.getElementById('signUpEmail').value;
    const password = document.getElementById('signUpPassword').value;

    createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            console.log('Account created:', userCredential.user);
            errorMessage.textContent = '';
            sendTokenToFlask(userCredential.user);
        })
        .catch((error) => {
            errorMessage.textContent = error.message;
            console.error('Error:', error);
        });
});

// Google Sign In
googleSignInBtn.addEventListener('click', () => {
    signInWithPopup(auth, provider)
        .then((result) => {
            console.log('Google sign in successful:', result.user);
            errorMessage.textContent = '';
            sendTokenToFlask(result.user);
        })
        .catch((error) => {
            errorMessage.textContent = error.message;
            console.error('Error:', error);
        });
});

// Sign Out
signOutBtn.addEventListener('click', () => {
    signOut(auth).then(() => {
        console.log('User signed out');
        fetch('/logout', { method: 'POST' });
    }).catch((error) => {
        console.error('Error signing out:', error);
    });
});

// Listen to authentication state changes
onAuthStateChanged(auth, (user) => {
    if (user) {
        whenSignedIn.style.display = 'block';
        whenSignedOut.style.display = 'none';
        signUpSection.style.display = 'none';
        
        document.getElementById('userName').textContent = user.displayName || 'User';
        document.getElementById('userEmail').textContent = user.email;
        document.getElementById('userUid').textContent = `UID: ${user.uid}`;
        
        if (user.photoURL) {
            document.getElementById('userPhoto').src = user.photoURL;
        } else {
            document.getElementById('userPhoto').src = 'https://via.placeholder.com/100';
        }
    } else {
        whenSignedIn.style.display = 'none';
        whenSignedOut.style.display = 'block';
    }
});

// Send token to Flask backend
function sendTokenToFlask(user) {
    user.getIdToken().then((idToken) => {
        fetch('/verify-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ idToken: idToken })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Backend response:', data);
        })
        .catch(error => {
            console.error('Error sending token to backend:', error);
        });
    });
}