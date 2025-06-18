import base64
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Load base64-encoded credentials from environment variable
b64_creds = os.getenv("GOOGLE_SHEETS_CREDS_B64")
creds_json = base64.b64decode(b64_creds).decode("utf-8")
creds_dict = json.loads(creds_json)

# Authorize with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("InventoryData").sheet1

# Get stock quantity
def get_stock(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Quantity']
    return "Product not found"

# Update stock or add new
def update_stock(product, store_id, change_qty, expiry_date, price, last_updated):
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            new_qty = int(row['Quantity']) + int(change_qty)
            sheet.update(f"C{idx}", new_qty)
            sheet.update(f"D{idx}", expiry_date)
            sheet.update(f"E{idx}", price)
            sheet.update(f"F{idx}", last_updated)
            return new_qty

    sheet.append_row([product, store_id, change_qty, expiry_date, price, last_updated])
    return change_qty

# Remove stock
def remove_stock(product, store_id, quantity):
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            current_qty = int(row['Quantity'])
            if current_qty <= int(quantity):
                sheet.delete_rows(idx)
                return f"🗑 Removed all {product} from Store {store_id}."
            else:
                new_qty = current_qty - int(quantity)
                sheet.update(f"C{idx}", new_qty)
                return f"➖ Removed {quantity} {product}(s). Remaining: {new_qty}."
    return f"❌ {product} not found in Store {store_id}."

# Get full inventory report
def get_full_stock(store_id):
    records = sheet.get_all_records()
    result = []
    for row in records:
        if str(row['Store ID']) == str(store_id):
            qty = row['Quantity'] if row['Quantity'] else '0'
            label = "NO STOCK" if int(qty) == 0 else f"{qty} units"
            result.append(f"{row['Product Name']}: {label}")
    return "\n".join(result) if result else "No products in store."

# Clear all inventory
def clear_all_products():
    all_values = sheet.get_all_values()
    if len(all_values) > 1:
        sheet.batch_clear([f"A2:F{len(all_values)}"])
        return "🧹 Cleared all inventory."
    return "Nothing to clear."

# Get unit price
def get_price(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Price'] or "Unknown"
    return "Price not found"

# Calculate total price for product
def calculate_total_price(product, store_id, quantity):
    price_str = get_price(product, store_id)
    if not price_str.startswith("$"):
        return "Invalid price format"
    try:
        unit_price = float(price_str[1:])
        total = unit_price * int(quantity)
        return f"${total:.2f}"
    except:
        return "Error in calculating total price"

# Combined price for multiple products
def calculate_combined_total(product_quantities, store_id):
    total = 0
    details = []
    for product, qty in product_quantities.items():
        price_str = get_price(product, store_id)
        if not price_str.startswith("$"):
            details.append(f"{product}: Invalid price")
            continue
        try:
            unit_price = float(price_str[1:])
            subtotal = unit_price * int(qty)
            total += subtotal
            details.append(f"{product} x{qty} = ${subtotal:.2f}")
        except:
            details.append(f"{product}: Error")
    details.append(f"Total = ${total:.2f}")
    return "\n".join(details)
