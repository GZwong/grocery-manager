import sys
sys.path.append("C:\Projects\grocery_manager")
order = SainsburysReceipt("./receipts/april_20_2023.pdf")
print(order.item_df)