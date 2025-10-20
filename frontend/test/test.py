from composio import Composio
from composio_gemini import GeminiProvider
from google import genai
from google.genai import types

# 1️⃣ Initialize Composio with GeminiProvider (not GoogleProvider)
composio = Composio(provider=GeminiProvider())

# Replace with your actual IDs
gmail_auth_config_id = "ac_dRUQLEQivdBI"
user_id = "pg-test-58d1a97b-1d1a-4fb2-8f5b-e87ce2f21266"

# 2️⃣ Start Gmail authentication
def authenticate_toolkit(user_id: str, auth_config_id: str):
    connection_request = composio.connected_accounts.initiate(
        user_id=user_id,
        auth_config_id=auth_config_id,
    )

    print(f"🔗 Visit this URL to authenticate Gmail:\n{connection_request.redirect_url}")
    connection_request.wait_for_connection(timeout=60)
    print("Gmail authenticated!")

    return connection_request.id

# Uncomment if not already connected
# connection_id = authenticate_toolkit(user_id, gmail_auth_config_id)

# 3️⃣ Get only the GMAIL_SEND_EMAIL tool (not drafts)
tools = composio.tools.get(user_id, tools=["GMAIL_SEND_EMAIL"])
print("[!] Tools retrieved:", len(tools), "tools available")
print("[!] Using GMAIL_SEND_EMAIL tool")

# 4️⃣ Initialize Gemini client
client = genai.Client()

# 5️⃣ Create proper tool config for Gemini
# GeminiProvider already converts tools to Gemini format
config = types.GenerateContentConfig(tools=tools)

# 6️⃣ Create chat and send Gmail action
chat = client.chats.create(model="gemini-2.0-flash", config=config)

# 7️⃣ Send a clear instruction to send email (not draft)
response = chat.send_message(
    "Send (do not draft) an email using Gmail to jaiminpansal78@gmail.com with subject 'Hey from Composio + Gemini!' and body 'This is a test message from my automation system.'"
)

# 8️⃣ Handle the response with function calls
print("[!] Response candidates:", response.candidates)

# Check if there are function calls in the response
if response.candidates and len(response.candidates) > 0:
    candidate = response.candidates[0]
    print(f"[!] Candidate content parts: {candidate.content.parts}")
    
    # Look for function calls
    for part in candidate.content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            function_call = part.function_call
            print(f"[!] Function call detected: {function_call.name}")
            print(f"[!] Function args: {function_call.args}")
            
            # Execute the function call using composio.tools.execute()
            try:
                # The tool slug is the function name, arguments are the params
                result = composio.tools.execute(
                    slug=function_call.name,
                    arguments=function_call.args,
                    user_id=user_id
                )
                print(f"[!] ✅ Tool executed successfully!")
                print(f"[!] Result: {result}")
            except Exception as e:
                print(f"[!] ❌ Error executing tool: {e}")
                import traceback
                traceback.print_exc()
        elif hasattr(part, 'text'):
            print(f"[!] Text response: {part.text}")