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
                {"role": "system", "content": "You are an inventory assistant helping small businesses manage stock and delivery."},
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
