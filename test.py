import pytesseract
from PIL import Image
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Temp\Tesseract-OCR\tessdata"

# Crea una imagen de prueba simple o usa una página del PDF
# Por ejemplo, genera una imagen con texto
from PIL import ImageDraw, ImageFont
img = Image.new('RGB', (400, 100), color='white')
d = ImageDraw.Draw(img)
d.text((10, 10), "Hola mundo, prueba de OCR", fill='black')
img.save("prueba_ocr.png")

texto = pytesseract.image_to_string(img, lang='spa')
print("Texto reconocido:", texto)