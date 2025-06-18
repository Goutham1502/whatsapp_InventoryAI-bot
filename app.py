from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from sheet_handler import (
    get_stock, update_stock, remove_stock,
    get_full_stock, clear_all_products,
    get_price, calculate_total_price, calculate_combined_total
)
import openai
import os
from datetime import datetime

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🧠 NLP-based parsing
def parse_user_input(user_input):
    prompt = f"""
You are an AI that extracts inventory instructions from WhatsApp messages.

Return ONLY a valid Python list of dictionaries. Each dictionary must include:
- intent: "add_stock", "remove_stock", "check_stock", "get_full_stock", "clear_all", "get_price", "calculate_total_price", "calculate_combined_total"
- product: string (optional for clear_all, get_full_stock)
- quantity: integer (optional or 0 if not mentioned)
- store_id: integer (default to 1 if not mentioned)
- expiry_date: string (optional)
- price: string (optional)
- last_updated: today's date if not mentioned
- product_quantities: dictionary for combined totals (optional)

Message: {repr(user_input)}


Example:
[
  {"intent": "add_stock", "product": "milk", "quantity": 5, "store_id": 1, "expiry_date": "2025-07-15", "price": "$2.50", "last_updated": "2025-06-17"},
  {"intent": "calculate_combined_total", "product_quantities": {"milk": 2, "bread": 3}, "store_id": 1}
]
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return eval(response.choices[0].message.content.strip())
    except Exception as e:
        print("[GPT Parse Error]", e)
        return None

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body")
    resp = MessagingResponse()
    msg = resp.message()

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
        product_quantities = parsed.get("product_quantities", {})

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
                cleared = clear_all_products()
                responses.append(cleared)

            elif intent == "get_price":
                unit_price = get_price(product, store_id)
                responses.append(f"🏷 Unit price of {product} in Store {store_id} is {unit_price}.")

            elif intent == "calculate_total_price":
                total = calculate_total_price(product, store_id, quantity)
                responses.append(f"💰 Total price for {quantity} {product}(s): {total}.")

            elif intent == "calculate_combined_total":
                total = calculate_combined_total(product_quantities, store_id)
                responses.append(total)

            else:
                responses.append(f"❌ Unrecognized intent: {intent}")
        except Exception as e:
            responses.append(f"❌ Error handling {product or 'item'}: {str(e)}")

    msg.body("\n".join(responses))
    return str(resp)

if __name__ == "__main__":
    app.run()
