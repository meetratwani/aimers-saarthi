import firebase_admin
from firebase_admin import credentials, auth
import os
from composio import ComposioToolSet, Action

# --- Firebase Initialization ---

try:
    cred = credentials.Certificate("/Users/jaiminpansal/Documents/programs/aimers/aimers-62228-firebase-adminsdk-fbsvc-910a61401c.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # It's common to check if the app is already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)


# --- Composio Initialization ---
# Make sure to set your COMPOSIO_API_KEY as an environment variable
composio_api_key = "ak_ZT4ra4hU8eJlKbokqlwJ"
if not composio_api_key:
    print("COMPOSIO_API_KEY environment variable not set.")
    exit()

composio_toolset = ComposioToolSet(api_key=composio_api_key)


def get_firebase_user_emails():
    """
    Fetches all user emails from Firebase Authentication.
    """
    print("Fetching user emails from Firebase...")
    try:
        users = auth.list_users().iterate_all()
        emails = [user.email for user in users if user.email]
        print(f"Found {len(emails)} user emails.")
        return emails
    except Exception as e:
        print(f"An error occurred while fetching Firebase users: {e}")
        return []

def send_email_with_composio(to_email, subject, body):
    """
    Sends an email using the Composio Gmail action.
    """
    print(f"Preparing to send email to: {to_email}")
    try:
        # Get the send email action from the Composio toolset
        send_email_action = composio_toolset.get_action(Action.GMAIL_SEND_EMAIL)

        if send_email_action:
            # Execute the action
            send_email_action(
                to=to_email,
                subject=subject,
                body=body
            )
            print(f"Successfully sent email to: {to_email}")
        else:
            print("GMAIL_SEND_EMAIL action not available. Make sure you have the Gmail tool enabled in Composio.")
    except Exception as e:
        print(f"An error occurred while sending the email with Composio: {e}")


if __name__ == "__main__":
    user_emails = get_firebase_user_emails()

    if user_emails:
        # Example: Send an email to the first user in the list
        first_email = user_emails[0]
        email_subject = "Hello from Composio and Firebase"
        email_body = "This is a test email sent from a Python script using Composio to send emails to users from Firebase."

        send_email_with_composio(first_email, email_subject, email_body)
    else:
        print("No user emails found in Firebase to send an email to.")