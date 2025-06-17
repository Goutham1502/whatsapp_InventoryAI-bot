from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from sheet_handler import get_stock, update_stock, remove_stock, get_full_stock, clear_all_products
import openai
import os
from datetime import datetime

app = Flask(__name__)

# ✅ Securely load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🧠 Extract intent, product, quantity, store_id from message
def parse_user_input(user_input):
    prompt = f"""
You are an AI that extracts inventory instructions from WhatsApp messages.

Return ONLY a valid Python dictionary with these keys:
- intent: "check_stock", "add_stock", "remove_stock", "get_full_stock", or "clear_all"
- product: string (optional if not needed)
- quantity: integer (default to 0)
- store_id: integer (default to 1)
- expiry_date: string (optional)
- price: string (optional)
- last_updated: string (optional)

Message: "{user_input}"

Example output:
{{"intent": "add_stock", "product": "chips", "quantity": 5, "store_id": 1, "expiry_date": "2025-07-01", "price": "$2.99", "last_updated": "2025-06-17"}}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return eval(response.choices[0].message.content.strip())
    except Exception as e:
        print("[GPT Error]", e)
        return None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body")
    resp = MessagingResponse()
    msg = resp.message()

    parsed = parse_user_input(incoming_msg)
    if not parsed:
        msg.body("❌ Sorry, I couldn't understand your request.")
        return str(resp)

    intent = parsed.get("intent")
    product = parsed.get("product")
    quantity = parsed.get("quantity", 0)
    store_id = parsed.get("store_id", 1)
    expiry_date = parsed.get("expiry_date", "")
    price = parsed.get("price", "")
    last_updated = parsed.get("last_updated", datetime.now().strftime("%Y-%m-%d"))

    try:
        if intent == "check_stock":
            stock = get_stock(product, store_id)
            msg.body(f"📦 {stock} units of {product} in Store {store_id}.")

        elif intent == "add_stock":
            new_qty = update_stock(product, store_id, quantity, expiry_date, price, last_updated)
            msg.body(f"✅ Added {quantity} {product}(s) to Store {store_id}. New total: {new_qty}.")

        elif intent == "remove_stock":
            result = remove_stock(product, store_id, quantity)
            msg.body(result)

        elif intent == "get_full_stock":
            report = get_full_stock(store_id)
            msg.body(report)

        elif intent == "clear_all":
            cleared = clear_all_products()
            msg.body(cleared)

        else:
            msg.body("❌ Unrecognized intent.")

    except Exception as e:
        msg.body(f"❌ Error: {str(e)}")

    return str(resp)

if __name__ == "__main__":
    app.run()
