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

# Ensure all required headers are present
REQUIRED_HEADERS = ["Product Name", "Store ID", "Quantity", "Expiry Date", "Price", "Last Updated"]
def ensure_headers():
    existing = sheet.row_values(1)
    if existing != REQUIRED_HEADERS:
        sheet.resize(1)
        sheet.append_row(REQUIRED_HEADERS)

ensure_headers()

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
            price = row['Price'] if row['Price'] else "$0"
            report += f"{row['Product Name']} - {qty} units @ {price}\n"
    return report.strip()

# Clear all products
def clear_all_products():
    sheet.resize(1)
    sheet.append_row(REQUIRED_HEADERS)
    return "🗑 All products cleared."

# Get unit price
def get_price(product, store_id):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            return row['Price']
    return "Price not found"

# Calculate total price for one product
def calculate_total_price(product, store_id, quantity):
    records = sheet.get_all_records()
    for row in records:
        if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
            try:
                unit_price = float(str(row['Price']).replace("$", "").strip())
                return f"${unit_price * quantity:.2f}"
            except:
                return f"Invalid price format for {product}"
    return "Product not found"

# Calculate combined total for multiple products
def calculate_combined_total(product_quantities, store_id):
    records = sheet.get_all_records()
    total = 0
    missing_items = []

    for product, qty in product_quantities.items():
        found = False
        for row in records:
            if row['Product Name'].lower() == product.lower() and str(row['Store ID']) == str(store_id):
                try:
                    unit_price = float(str(row['Price']).replace("$", "").strip())
                    total += unit_price * qty
                    found = True
                    break
                except:
                    return f"Invalid price format for {product}"
        if not found:
            missing_items.append(product)

    response = f"🧾 Combined total: ${total:.2f}"
    if missing_items:
        response += f"\nMissing or not found: {', '.join(missing_items)}"
    return response
