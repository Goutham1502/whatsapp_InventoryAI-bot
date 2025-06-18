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

# Update stock (stock in)
def update_stock(product, store_id, change_qty, expiry_date, price, last_updated):
    product = str(product).strip()
    store_id = str(store_id).strip()
    records = sheet.get_all_records()

    for idx, row in enumerate(records):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == store_id:
            row_num = idx + 2
            new_qty = int(row['Quantity']) + int(change_qty)
            sheet.update_cell(row_num, 3, new_qty)
            sheet.update_cell(row_num, 4, expiry_date)
            sheet.update_cell(row_num, 5, price)
            sheet.update_cell(row_num, 6, last_updated)
            return new_qty

    # Add new row if not found
    new_row = [product, store_id, change_qty, expiry_date, price, last_updated]
    sheet.append_row(new_row)
    return change_qty

# Remove stock
def remove_stock(product, store_id, qty):
    records = sheet.get_all_records()
    for idx, row in enumerate(records):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            row_num = idx + 2
            current_qty = int(row['Quantity'])
            new_qty = current_qty - int(qty)
            if new_qty <= 0:
                sheet.delete_row(row_num)
                return f"🗑 Removed all {product} from Store {store_id}."
            else:
                sheet.update_cell(row_num, 3, new_qty)
                return f"➖ Removed {qty} {product}(s). Remaining: {new_qty}."
    return f"❌ {product} not found in Store {store_id}."

# Get full stock
def get_full_stock(store_id):
    records = sheet.get_all_records()
    report = ""
    for row in records:
        if str(row['Store ID']) == str(store_id):
            report += f"{row['Product Name']}: {row['Quantity']} units (Price: {row['Price ']}, Exp: {row['Expiry Date']})\n"
    return report.strip() if report else "No data available."

# Clear all products
def clear_all_products():
    sheet.resize(rows=1)
    return "🧹 Cleared all product rows."

# Get price per unit
def get_price(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Price ']
    return "Price not found"

# Calculate total price for given quantity
def calculate_total_price(product, store_id, qty):
    unit_price = get_price(product, store_id)
    if unit_price == "Price not found":
        return unit_price
    try:
        unit_value = float(unit_price.replace("$", "").strip())
        return f"${round(unit_value * int(qty), 2)}"
    except:
        return "Error calculating price"
