import base64
import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load base64-encoded credentials from environment variable
b64_creds = """<ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAi
c2FuZ3JhaGFpIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiMWNjODNhNGUwMDIzYmRi
ZTliNmZjZTA3NzEwM2YwNWZmOWQ1ODg3MSIsCiAgInByaXZhdGVfa2V5IjogIi0t
LS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZRSUJBREFOQmdrcWhraUc5
dzBCQVFFRkFBU0NCS2N3Z2dTakFnRUFBb0lCQVFDK0ZhVStrUVpzYzRJdFxuUUtj
d29lYVJJclNieE5PS3A2ZHEyRkViQ1ArSG9wTDhsUVVRRjkyV0lUK21GaDNkc0VM
Nm9MT0s2WHgvQ29zL1xuS0NCZVNiMHQyRGpqVFBUT3lkQm1Pa1BOMWk2c01yY3hT
ZzA1QWhkSTk2bm5SZHhBbDVkOFNudVYxaFRIRnRnNFxuejFFTG9SMWtRdzFzOFVo
bHI1OERCMmZxRlM4ZTBKczBpSXhLOFdqTmsvNHcwRUFZTEV4aU9ZWFFqakJLZldu
T1xuNm04YUM1eXgzaHpXQnBtRXVUVS9UeU5SdlhCY1hWMGF2NUVRVGx6MkJpRFdJ
UndQa3EyNjk5amFDS3c4U0FCNVxuaFBlOGphYW8wS1JxZEJYSzZXUXNHNEE5S25Z
dEhJN1ViRFhuZGVOTm16N3FlRGg5anhDQ0RpN3RZb1MrdXN0VVxuTzkvUkJvQm5B
Z01CQUFFQ2dnRUFNM1dNcktsNlFiWHJrZkNrMG1laUVieUJoSUgrZXRUMFg5cDc2
b08vR2FzTFxuZTlHajh6MWl3WmZ5c1RYZmsvcDV4M3ZsM3o5aWNzb1o5RmthbWl3
QVNQNzJONkxIeTR1YkhYRzhsV2JjYjhXelxuRG1icnVYazFjSTJMczQ2WUYreHlH
RFhaeXpDUG8yNHR6d05nLzNMNGtBSVBDbVV2b2tldkZwVFVydXhaTzAvcVxub25p
QXB6QTRHL2VrYnFsdmZycGZqcHlqU0dRMGhPNGRtWTJ1NlVZaHROQnhEUDloMUdu
K2p2S0VXN1RmaTRyVFxuUjREYy9xSHZXcVBtWmovRVF1dUwzWEliWWRaSzVzQ0tH
ZlQ3K1hEYU5sZWtvaldCbkdkdjdBOG9nSkdLbEVvZlxuWWpNdjZRcGsvVlZqd1hO
aE9mZkxhQzI5NjNBVG5HWURDSGlBV0w1NlFRS0JnUURlN0N2K1pxekZyYjBEZTFO
Q1xucTZQd1ZDSzJyRFRtdjM3M0hrZUx6Y3lSUDVMUG5Ec2g1MFBuaU9hU1EyMmRU
WXQzNndBRERDb1JGNVloV1NEcFxuTDhIN0xINXpYdmUrVlh4cmt2QlZkaE5malpF
WXFGcmp2eGlpK01heW1rV0R2eE9FdmpWWEx6MUdBei9VVms5dVxuM1FtRjBmQ3p4
YWhucnpiRUFVd3NSdmd5dHdLQmdRRGFTaHNBV09aZU5XWjhHcXFrSW53WFBrQWJT
Sm9XNFhHT1xuSTRmWFZqZFRVWHI2SnNWbEpocVBTeGsrN0M4TmJvbHJ0OWRFMXVE
LzRKVncxelZ2UEVkK3J5dTZOWGNUaEhSNVxueEZiWmlFcCthUDUwOW1NaDZuQzlP
YkY4d0VWdWpRVE5UcGhEc05RKzN1bTZpRWhERWp5UmxkM1kvQkNXQnQwZlxuSjE0
SzloYXYwUUtCZ1FEQWZWSm50Q1VQOUx1M20vQURLODY5b1Fqd2o3YUdZV2l5M2ZT
TnBjRTAwcDVrb3RUMFxucTR1WkREOThvTGl3RWR1U1N0dVJ4aGswOVJidjZOUmdS
cHJMMWxuQ0tZam5VMDNDWGZrazhuWThGalBxQk1XbVxuenNYcFE4UGZTUk1wZGY3
V3FwL0lqc1BzQnJaQkZkNDFMcXdnWDIzbTdaQkRKNnEwaVNKTFFXVGo5UUtCZ0hH
Qlxub3pTMUJXVHJZNVVZMEs1MGVBNG1Bbk90ZHVKNjYrODdMb0djaFR3LzNEQ0RS
SlZxRU5sOTlXeXdwMjdXa1lKL1xubitKZDBiVjc5SGt1anN4K2piYWtJNXE1L21j
WnN1ODJWdXJhWWRJRmluc0xPMVVCY1FvVUcrU0FuaG4wSGhFYlxuMHpVdmw4M3hY
NXZ0RFpaQ3YxZjhrOVVtalFGV0pGajB3WVAxbnFwaEFvR0FjVFJ5eXdYRTdCczlV
eTBJcFBjK1xudFJZNmk4SnZuSzZ4MStNTXkzdGc4K3RYL2pacnBxbFRHOUN3NUF6
cmZVSWgxZ1FtYkhRV3Z3eVpiaEd6VTRDVVxubU1iK2tZUk9aZ0RuMWVhQzdudDdD
TDNEK3oyMldmbWZDVUNCWEhidFZqNGg3Wk40TmxHaGVLY2k3QWxPWkFCcFxuS0xJ
NVVXaWxHeCtWOVptaDA0TlR5Ums9XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0t
XG4iLAogICJjbGllbnRfZW1haWwiOiAic2FuZ3JhaGFpQHNhbmdyYWhhaS5pYW0u
Z3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDkwOTEwMDAy
MjMzMDE5ODI3OTIiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdv
b2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczov
L29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJf
eDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0
aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczov
L3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L3Nhbmdy
YWhhaSU0MHNhbmdyYWhhaS5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVu
aXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo=>""".strip()  # You added this in Render
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

# Update stock (e.g. stock in/out)
def update_stock(product, store_id, change_qty):
    cell = sheet.find(product)
    row = cell.row
    current_qty = int(sheet.cell(row, 3).value)
    new_qty = current_qty + change_qty
    sheet.update_cell(row, 3, new_qty)
    return new_qty
