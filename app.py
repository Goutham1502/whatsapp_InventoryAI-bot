from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai

app = Flask(__name__)
openai.api_key = "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"

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get('Body')
    try:
        gpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for managing inventory and deliveries."},
                {"role": "user", "content": incoming_msg}
            ],
            max_tokens=100
        )
        reply = gpt_response.choices[0].message.content.strip()
    except:
        reply = "Sorry, I couldn't respond right now."

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run()
