from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from sheet_handler import get_stock, update_stock
import openai
import os

app = Flask(__name__)

# Use your environment variable in Render
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_user_input(user_input):
    prompt = f"""
    Extract this information from the message: 
    - intent: check_stock or add_stock
    - product name
    - quantity (0 if not mentioned)
    - store_id (default to 1 if not mentioned)

    Return a valid Python dictionary.

    Message: "{user_input}"
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return eval(response.choices[0].message.content.strip())
    except:
        return None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body")
    resp = MessagingResponse()
    msg = resp.message()

    parsed = parse_user_input(incoming_msg)

    if not parsed:
        msg.body("Sorry, I couldn't understand your request.")
        return str(resp)

    intent = parsed.get("intent")
    product = parsed.get("product")
    quantity = parsed.get("quantity", 0)
    store_id = parsed.get("store_id", 1)

    try:
        if intent == "check_stock":
            stock = get_stock(product, store_id)
            msg.body(f"{stock} units of {product} in Store {store_id}.")

        elif intent == "add_stock":
            new_qty = update_stock(product, store_id, quantity)
            msg.body(f"Added {quantity} {product}(s) to Store {store_id}. New total: {new_qty}.")

        else:
            msg.body("Sorry, I couldn’t process your request.")
    except Exception as e:
        msg.body(f"Error: {str(e)}")

    return str(resp)

if __name__ == "__main__":
    app.run()
