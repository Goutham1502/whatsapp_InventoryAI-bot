from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from sheet_handler import get_stock, update_stock, remove_stock, get_full_stock
import openai
import os

app = Flask(__name__)

# ✅ Securely load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🧠 Extract full inventory fields from user's message
def parse_user_input(user_input):
    prompt = f"""
You are an AI that extracts inventory instructions from messages.

Extract this info and return ONLY a valid Python dictionary with:
- intent: one of ["check_stock", "add_stock", "remove_stock", "get_full_stock_report"]
- product: string ("" if not needed)
- quantity: integer (0 if not mentioned)
- store_id: integer (1 if not mentioned)
- expiry_date: string ("YYYY-MM-DD" or "" if not mentioned)
- price: float (0 if not mentioned)
- last_updated: today's date in YYYY-MM-DD format

Message: "{user_input}"

Example output:
{{"intent": "add_stock", "product": "chips", "quantity": 5, "store_id": 1, "expiry_date": "2025-07-01", "price": 2.5, "last_updated": "2025-06-16"}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        parsed = eval(response.choices[0].message.content.strip())
        print("[DEBUG] Parsed GPT Output:", parsed)
        return parsed
    except Exception as e:
        print("[GPT Error]", e)
        return None

# 📲 Handle incoming WhatsApp messages
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
    price = parsed.get("price", 0)
    last_updated = parsed.get("last_updated", "")

    try:
        if intent == "check_stock":
            stock = get_stock(product, store_id)
            msg.body(f"{stock} units of {product} in Store {store_id}.")

        elif intent == "add_stock":
            new_qty = update_stock(product, store_id, quantity, expiry_date, price, last_updated)
            msg.body(f"✅ Added {quantity} {product}(s) to Store {store_id}. New total: {new_qty}.")

        elif intent == "remove_stock":
            result = remove_stock(product, store_id, quantity)
            msg.body(result)

        elif intent == "get_full_stock_report":
            summary = get_full_stock(store_id)
            msg.body(summary)

        else:
            msg.body("❌ Intent not recognized.")

    except Exception as e:
        msg.body(f"❌ Error: {str(e)}")

    return str(resp)

if __name__ == "__main__":
    app.run()
