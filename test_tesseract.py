import os
import pytesseract
from PIL import Image
import pymupdf

# Configuración fija fuera de OneDrive y sin tildes
pytesseract.pytesseract.tesseract_cmd = r"C:\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Tesseract-OCR\tessdata"

# Verificar si ahora sí detecta los idiomas correctamente
print("Idiomas disponibles:", pytesseract.get_languages(config=''))

# Procesar el PDF de prueba
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "test31.pdf")

if os.path.exists(pdf_path):
    doc = pymupdf.open(pdf_path)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=300)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    texto = pytesseract.image_to_string(img, lang='spa', config='--psm 3 --oem 1')
    print("--- TEXTO EXTRAÍDO (primeros 1000 caracteres) ---")
    print(texto[:1000])
    print("--- FIN DEL TEXTO ---")
else:
    print(f"⚠️ No se encontró el archivo test31.pdf en {base_dir}")