import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import base64
import json
import os

# ✅ Load base64 credentials from environment (Render)
b64_creds = os.getenv("GOOGLE_SHEETS_CREDS")  # Make sure this matches your Render environment variable name
creds_json = base64.b64decode(b64_creds).decode("utf-8")
creds_dict = json.loads(creds_json)

# ✅ Setup credentials and sheet connection
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("InventoryData").sheet1

# ✅ Get available stock for a product
def get_stock(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Quantity']
    return "Product not found"

# ✅ Add or update stock with extra fields
def update_stock(product, store_id, change_qty, expiry_date, price, last_updated):
    product = str(product).strip()
    store_id = str(store_id).strip()
    found = False
    cell = None

    try:
        cell = sheet.find(product)
    except:
        cell = None

    if cell:
        row = cell.row
        current_qty = int(sheet.cell(row, 3).value)
        new_qty = current_qty + change_qty
        sheet.update_cell(row, 3, new_qty)
        sheet.update_cell(row, 4, expiry_date)
        sheet.update_cell(row, 5, price)
        sheet.update_cell(row, 6, last_updated)
        return new_qty
    else:
        # Append new row if product doesn't exist
        new_row = [product, store_id, change_qty, expiry_date, price, last_updated]
        sheet.append_row(new_row)
        return change_qty

# ✅ Remove stock or delete row if quantity = 0
def remove_stock(product, store_id, remove_qty):
    product = str(product).strip()
    try:
        cell = sheet.find(product)
        if not cell:
            return "❌ Product not found."
        row = cell.row
        current_qty = int(sheet.cell(row, 3).value)
        new_qty = current_qty - remove_qty

        if new_qty > 0:
            sheet.update_cell(row, 3, new_qty)
            return f"✅ Removed {remove_qty} {product}(s) from Store {store_id}. New total: {new_qty}."
        else:
            sheet.delete_rows(row)
            return f"🗑️ {product} stock is now 0 and removed from Store {store_id}."
    except:
        return "❌ Error while removing stock."

# ✅ Return full inventory summary
def get_full_stock(store_id):
    records = sheet.get_all_records()
    summary = f"📦 Stock Report for Store {store_id} (Product: Quantity):\n"
    for row in records:
        if str(row['Store ID']) == str(store_id):
            summary += f"- {row['Product']}: {row['Quantity']}\n"
    return summary if "-" in summary else "No stock found for this store."
