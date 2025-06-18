import base64
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load base64-encoded credentials from environment variable
b64_creds = os.getenv("GOOGLE_SHEETS_CREDS_B64")
creds_json = base64.b64decode(b64_creds).decode("utf-8")
creds_dict = json.loads(creds_json)

# Authorize with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("InventoryData").sheet1

# Read stock

def get_stock(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Quantity']
    return "Product not found"

# Update stock

def update_stock(product, store_id, change_qty, expiry_date="", price="", last_updated=""):
    product = str(product).strip()
    store_id = str(store_id).strip()
    found = False
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == store_id:
            current_qty = int(row['Quantity'])
            new_qty = current_qty + change_qty
            sheet.update_cell(idx, 3, new_qty)  # Quantity
            sheet.update_cell(idx, 4, expiry_date)
            sheet.update_cell(idx, 5, price)
            sheet.update_cell(idx, 6, last_updated)
            found = True
            return new_qty

    if not found:
        new_row = [product, store_id, change_qty, expiry_date, price, last_updated]
        sheet.append_row(new_row)
        return change_qty

# Remove stock

def remove_stock(product, store_id, quantity):
    product = str(product).strip()
    store_id = str(store_id).strip()
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == store_id:
            current_qty = int(row['Quantity'])
            new_qty = current_qty - quantity
            if new_qty > 0:
                sheet.update_cell(idx, 3, new_qty)
                return f"✅ Removed {quantity} {product}(s). Remaining: {new_qty}."
            else:
                sheet.delete_row(idx)
                return f"✅ Removed all {product} from Store {store_id}."
    return f"❌ {product} not found in Store {store_id}."

# Get full stock

def get_full_stock(store_id):
    records = sheet.get_all_records()
    report = ""
    for row in records:
        if str(row['Store ID']) == str(store_id):
            qty = row['Quantity'] if row['Quantity'] else "NO STOCK"
            report += f"{row['Product Name']} - {qty}\n"
    return report.strip()

# Clear all products

def clear_all_products():
    existing = sheet.get_all_values()
    headers = existing[0] if existing else []
    sheet.resize(1)
    sheet.append_row(headers)
    return "🗑 All products cleared."

# Get unit price

def get_price(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Price']
    return "Price not found"

# Calculate total price

def calculate_total_price(product, store_id, quantity):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            try:
                unit_price = float(row['Price'].replace("$", ""))
                return f"${unit_price * quantity:.2f}"
            except:
                return "Invalid price format"
    return "Product not found"
