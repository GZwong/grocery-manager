from pypdf import PdfReader

reader = PdfReader('./receipts/july_14_2023.pdf')

page1 = reader.pages[0]
print(page1.extract_text())