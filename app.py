from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    resp = MessagingResponse()
    resp.message("✅ Your bot is working!")
    return str(resp)

if __name__ == "__main__":
    app.run()
