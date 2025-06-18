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

def get_active_sheet():
    from datetime import datetime
    month = datetime.now().strftime("%B_%Y")
    try:
        return client.open("InventoryData").worksheet(month)
    except:
        sheet = client.open("InventoryData").add_worksheet(title=month, rows="1000", cols="10")
        sheet.append_row(["Product Name", "Store ID", "Quantity", "Expiry Date", "Price", "Last Updated"])
        return sheet

def get_stock(product, store_id):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Quantity']
    return "Product not found"

def update_stock(product, store_id, change_qty, expiry_date, price, last_updated):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            new_qty = int(row['Quantity']) + change_qty
            sheet.update_cell(idx, 3, new_qty)
            sheet.update_cell(idx, 4, expiry_date)
            sheet.update_cell(idx, 5, price)
            sheet.update_cell(idx, 6, last_updated)
            return new_qty
    sheet.append_row([product, store_id, change_qty, expiry_date, price, last_updated])
    return change_qty

def remove_stock(product, store_id, quantity):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    for idx, row in enumerate(records, start=2):
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            current_qty = int(row['Quantity'])
            if current_qty <= quantity:
                sheet.delete_row(idx)
                return f"🗑 Removed all {product} from Store {store_id}."
            else:
                new_qty = current_qty - quantity
                sheet.update_cell(idx, 3, new_qty)
                return f"➖ Removed {quantity} {product}(s). Remaining: {new_qty}."
    return f"❌ {product} not found in Store {store_id}."

def get_full_stock(store_id):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    report = []
    for row in records:
        if str(row['Store ID']) == str(store_id):
            q = row['Quantity']
            status = "NO STOCK" if int(q) <= 0 else f"{q} units"
            report.append(f"{row['Product Name']}: {status}")
    return "\n".join(report) if report else "No data found."

def clear_all_products():
    sheet = get_active_sheet()
    sheet.resize(rows=1)
    sheet.append_row(["Product Name", "Store ID", "Quantity", "Expiry Date", "Price", "Last Updated"])
    return "🧹 All inventory cleared."

def get_price(product, store_id):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Price']
    return "Not Found"

def calculate_total_price(product, store_id, quantity):
    unit_price = get_price(product, store_id)
    if unit_price == "Not Found":
        return unit_price
    try:
        value = float(unit_price.replace("$", "")) * quantity
        return f"${value:.2f}"
    except:
        return "Invalid price format"

def calculate_combined_total(product_quantities, store_id):
    sheet = get_active_sheet()
    records = sheet.get_all_records()
    total = 0.0
    lines = []
    for product, qty in product_quantities.items():
        price_str = get_price(product, store_id)
        try:
            price_val = float(price_str.replace("$", ""))
            subtotal = price_val * qty
            total += subtotal
            lines.append(f"{product}: {qty} x {price_val:.2f} = ${subtotal:.2f}")
        except:
            lines.append(f"{product}: Invalid price format")
    lines.append(f"Total: ${total:.2f}")
    return "\n".join(lines)
