from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from sheet_handler import get_stock, update_stock, remove_stock, get_full_stock, clear_all_products, get_price, calculate_total_price
import openai
import os
from datetime import datetime

app = Flask(__name__)

# ✅ Securely load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🧠 Extract inventory actions from WhatsApp message
def parse_user_input(user_input):
    prompt = f"""
You are an AI that extracts multiple inventory instructions from WhatsApp messages.

Return ONLY a valid Python list of dictionaries. Each dictionary should contain:
- intent: one of ["add_stock", "remove_stock", "check_stock", "get_full_stock", "clear_all", "get_price", "calculate_total_price"]
- product: string (optional for get_full_stock or clear_all)
- quantity: integer (0 if not mentioned)
- store_id: integer (default to 1 if not mentioned)
- expiry_date: string (optional)
- price: string (optional)
- last_updated: string (default to today if not mentioned)

Example input: "Clear all inventory"
Example output: [{{"intent": "clear_all"}}]

Example input: "Add 15 milk (expires July 30, price $2.50), 10 bread (expires July 25, price $1.50), 5 yogurt (exp Aug 5, $3), and 8 eggs (Aug 2, $4.20) to store 1. Also add 20 bananas ($1), 12 apples ($1.80), and 6 orange juice (exp Aug 10, $3.60) to store 2. Add 10 chips, 5 cookies ($2.25), and 7 butter packs ($3.10) to store 1."
Example output:
[
  {{"intent": "add_stock", "product": "milk", "quantity": 15, "store_id": 1, "expiry_date": "2025-07-30", "price": "$2.50"}},
  {{"intent": "add_stock", "product": "bread", "quantity": 10, "store_id": 1, "expiry_date": "2025-07-25", "price": "$1.50"}},
  {{"intent": "add_stock", "product": "yogurt", "quantity": 5, "store_id": 1, "expiry_date": "2025-08-05", "price": "$3"}},
  {{"intent": "add_stock", "product": "eggs", "quantity": 8, "store_id": 1, "expiry_date": "2025-08-02", "price": "$4.20"}},
  {{"intent": "add_stock", "product": "bananas", "quantity": 20, "store_id": 2, "price": "$1"}},
  {{"intent": "add_stock", "product": "apples", "quantity": 12, "store_id": 2, "price": "$1.80"}},
  {{"intent": "add_stock", "product": "orange juice", "quantity": 6, "store_id": 2, "expiry_date": "2025-08-10", "price": "$3.60"}},
  {{"intent": "add_stock", "product": "chips", "quantity": 10, "store_id": 1}},
  {{"intent": "add_stock", "product": "cookies", "quantity": 5, "store_id": 1, "price": "$2.25"}},
  {{"intent": "add_stock", "product": "butter packs", "quantity": 7, "store_id": 1, "price": "$3.10"}}
]

Message: "{user_input}"
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
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

    if incoming_msg.lower().strip() == "confirm clear all inventory":
        msg.body(clear_all_products())
        return str(resp)

    parsed_list = parse_user_input(incoming_msg)
    if not parsed_list or not isinstance(parsed_list, list):
        msg.body("❌ Sorry, I couldn't understand your request.")
        return str(resp)

    responses = []
    for parsed in parsed_list:
        intent = parsed.get("intent")
        product = parsed.get("product", "")
        quantity = parsed.get("quantity", 0)
        store_id = parsed.get("store_id", 1)
        expiry_date = parsed.get("expiry_date", "")
        price = parsed.get("price", "")
        last_updated = parsed.get("last_updated", datetime.now().strftime("%Y-%m-%d"))

        try:
            if intent == "check_stock":
                stock = get_stock(product, store_id)
                responses.append(f"📦 {stock} units of {product} in Store {store_id}.")

            elif intent == "add_stock":
                new_qty = update_stock(product, store_id, quantity, expiry_date, price, last_updated)
                responses.append(f"✅ Added {quantity} {product}(s) to Store {store_id}. New total: {new_qty}.")

            elif intent == "remove_stock":
                result = remove_stock(product, store_id, quantity)
                responses.append(result)

            elif intent == "get_full_stock":
                report = get_full_stock(store_id)
                responses.append("📊 Full Stock Report:\n" + report)

            elif intent == "clear_all":
                responses.append("⚠️ Please confirm to clear all inventory by replying with: confirm clear all inventory")

            elif intent == "get_price":
                unit_price = get_price(product, store_id)
                responses.append(f"🏷 Price of {product} in Store {store_id} is {unit_price}.")

            elif intent == "calculate_total_price":
                total = calculate_total_price(product, store_id, quantity)
                responses.append(f"💰 Total price for {quantity} {product}(s) in Store {store_id} is {total}.")

            else:
                responses.append(f"❌ Unrecognized intent for {product}.")

        except Exception as e:
            responses.append(f"❌ Error handling {product}: {str(e)}")

    msg.body("\n".join(responses))
    return str(resp)

if __name__ == "__main__":
    app.run()
