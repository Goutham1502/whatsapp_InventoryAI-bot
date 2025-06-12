from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

app = Flask(__name__)

# ✅ Load API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get('Body')
    
    try:
        if not openai.api_key:
            raise ValueError("API key not loaded")

       gpt_response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": """
You are an AI assistant that manages a store's inventory and deliveries.
Your job is to:
- Add stock when the user says things like "Add 10 Soap"
- Remove stock when they say "Sold 5 Milk"
- Log the product name, quantity, and action
- Reply in a friendly tone
- Keep responses short and professional
Do NOT respond if the message is unrelated to inventory, delivery, or stock. 
If you're not sure, reply: 'Sorry, I can only help with inventory or delivery updates.'
"""},
        {"role": "user", "content": incoming_msg}
    ],
    max_tokens=100
)

        reply = gpt_response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT ERROR:", str(e))  # This will show in Render logs
        reply = "Sorry, I couldn't respond right now."

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run()
