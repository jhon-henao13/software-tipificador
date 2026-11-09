# clasificador_ia.py — Versión con Razonamiento LLM Local (Ollama)
import os
import re
import json
import requests
import pymupdf
import pytesseract
from PIL import Image
import cv2
import numpy as np

class ClasificadorDocumentosIA:
    def __init__(self, model_name="llama3.2"):
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Configurar Tesseract como respaldo robusto
        ruta_tesseract = r"C:\Tesseract-OCR\tesseract.exe"
        if os.path.exists(ruta_tesseract):
            pytesseract.pytesseract.tesseract_cmd = ruta_tesseract

    def _consultar_ia_local(self, texto_documento):
        """Envía el texto extraído al modelo local en Ollama para razonamiento estructurado."""
        prompt = f"""
Eres un auditor de facturación médica de Genhospi S.A.S.
Analiza el texto de una página de un paquete de facturación y extrae EXACTAMENTE estos campos.

REGLAS CRÍTICAS:
- "tipo": 
  * "CRC" si el texto contiene "ACTA DE ENTREGA" o "FACTURA ELECTRÓNICA DE VENTA" o el logo de Genhospi.
  * "OPF" si contiene "P-AUTORIZACIÓN DE SERVICIOS DE SALUD" o "INFORME DE AUTORIZACIÓN EN LÍNEA" o "SERVICIO OCCIDENTAL DE SALUD" sin logo de Genhospi.
  * "OTRO" en caso contrario.
- "numero_factura": SOLO el número que sigue inmediatamente a "FVCE" en la parte superior derecha del documento (ej. "FVCE394174" → "394174"). NO uses números de autorización (suelen empezar por 45...), NO uses el NIT de la EPS (805001157), NO uses el CUFE (cadena larga alfanumérica), NO uses el Res. DIAN. Si no aparece "FVCE" seguido de 6–8 dígitos, devuelve null.
- "paciente": El nombre completo de la persona afiliada. Búscalo junto a "Paciente", "Afiliado", "Nombre del Paciente" o en el campo "DATOS DEL PACIENTE". NO uses el nombre de la EPS, ni el de Genhospi, ni el del médico.
- "identificacion": El número de cédula del paciente (6–10 dígitos), sin puntos. Búscalo junto a "Identificación", "C.C.", "Documento" o "Afiliado". NO uses NIT, NO uses números de autorización.

Devuelve SOLO un objeto JSON válido con esta estructura exacta (sin texto adicional):
{{
  "tipo": "CRC" | "OPF" | "OTRO",
  "numero_factura": "string o null",
  "paciente": "string o null",
  "identificacion": "string o null"
}}

Texto de la página:
---
{texto_documento[:3000]}
---
"""
        payload = {
            "model": "qwen2.5:3b-instruct",  # ← Cambia el modelo aquí
            "prompt": prompt,
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["CRC", "OPF", "OTRO"]},
                    "numero_factura": {"type": ["string", "null"]},
                    "paciente": {"type": ["string", "null"]},
                    "identificacion": {"type": ["string", "null"]}
                },
                "required": ["tipo", "numero_factura", "paciente", "identificacion"]
            },
            "options": {"temperature": 0.0}  # 0.0 para máxima determinación
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=45)
            if response.status_code == 200:
                resultado_json = response.json().get("response", "{}")
                return json.loads(resultado_json)
        except Exception as e:
            print(f"Aviso: Ollama no respondió o no está activo ({e}). Usando motor heurístico avanzado de respaldo.")
        
        return None

    # clasificador_ia.py — Método analizar_pagina mejorado
    def analizar_pagina(self, imagen_pil, texto_nativo=None):
        try:
            # 1. Si hay texto nativo suficiente, úsalo directamente
            if texto_nativo and len(texto_nativo.strip()) >= 50:
                texto = texto_nativo
                print(f"✅ Texto nativo extraído ({len(texto)} caracteres). Omitiendo OCR.")
            else:
                # 2. Fallback: OCR de alta calidad solo si el PDF es escaneado
                img_cv = cv2.cvtColor(np.array(imagen_pil), cv2.COLOR_RGB2BGR)
                gris = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                gris = cv2.bilateralFilter(gris, 9, 75, 75)
                binaria = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 31, 11)
                img_procesada = Image.fromarray(binaria)
                texto = pytesseract.image_to_string(img_procesada, lang='spa',
                                                    config='--psm 3 --oem 1')
                print(f"⚠️ OCR ejecutado ({len(texto)} caracteres).")

            texto_upper = texto.upper()

            # 3. Intentar razonamiento con IA Local (Ollama)
            datos_ia = self._consultar_ia_local(texto)

            if datos_ia and datos_ia.get("tipo") in ["CRC", "OPF"]:
                return {
                    "tipo": datos_ia.get("tipo"),
                    "numero_factura": datos_ia.get("numero_factura"),
                    "paciente": datos_ia.get("paciente", "Desconocido"),
                    "identificacion": datos_ia.get("identificacion")
                }

            # 4. Respaldo heurístico robusto si la IA local no está corriendo
            es_crc = any(k in texto_upper for k in [
                "ACTA DE ENTREGA",
                "SERVICIO OCCIDENTAL DE SALUD",
                "FACTURA ELECTRÓNICA DE VENTA"
            ])
            es_opf = any(k in texto_upper for k in [
                "P-AUTORIZACIÓN DE SERVICIOS DE SALUD",
                "INFORME DE AUTORIZACIÓN"
            ])
            tipo = "CRC" if es_crc else ("OPF" if es_opf else "OTRO")

            m_factura = re.search(r'FVCE\s*([0-9OIZSB]{5,8})', texto, re.IGNORECASE)
            factura = None
            if m_factura:
                raw = m_factura.group(1)
                factura = (raw.replace('O', '0')
                              .replace('I', '1')
                              .replace('Z', '2')
                              .replace('S', '5')
                              .replace('B', '8'))

            m_id = re.search(
                r'(?:Identificación|C\.?C\.?|Documento|ID|Afiliado)\s*[:\-]?\s*([\d\.]{6,12})',
                texto, re.IGNORECASE
            )
            paciente_id = re.sub(r'[^\d]', '', m_id.group(1)) if m_id else None

            return {
                "tipo": tipo,
                "numero_factura": factura,
                "paciente": "Desconocido",
                "identificacion": paciente_id
            }
        except Exception as e:
            print(f"Error analizando página con IA: {e}")
            return {"tipo": "OTRO", "numero_factura": None,
                    "paciente": "Desconocido", "identificacion": None}