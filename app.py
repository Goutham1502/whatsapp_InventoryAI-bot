from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai

app = Flask(__name__)
openai.api_key = "sk-your-openai-key"  # Replace this with your real OpenAI API key

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
