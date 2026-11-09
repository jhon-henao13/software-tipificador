# Genhospi - Sistema Inteligente de Tipificación y Auditoría (Autotipificador AI)

Solución de software de escritorio avanzada desarrollada en **Python y CustomTkinter** para automatizar, clasificar y estructurar de forma inteligente lotes masivos de documentos PDF médicos (Facturas, Actas de Entrega / CRC, Soportes / OPF y Autorizaciones) orientada al equipo de auditoría de Genhospi.

---

## 📋 ¿Qué es?

Es una herramienta de doble modalidad (Tipificación Manual Interactiva y Autotipificación IA Avanzada) diseñada para procesar documentos de salud complejos de EPS (como SOS, Sanitas, Emssanar, Asmet Salud), extrayendo automáticamente números de factura, nombres de pacientes y asociando páginas mediante técnicas de procesamiento de lenguaje natural y visión artificial.

---

## 🛑 ¿Qué problema resuelve?

La recepción de lotes masivos de documentos en PDF multicliente o multi-factura suele requerir que los auditores revisen página por página de forma manual para separar actas, fórmulas y soportes. Esto genera:
- Desperdicio masivo de tiempo operativo ordenando y renombrando archivos PDF.
- Errores humanos al asociar soportes a facturas incorrectas.
- Dificultad para mantener una jerarquía estricta de carpetas de radicación por fecha, EPS y modalidad de contrato.

---

## ⚡ ¿Qué hace el sistema?

1. **Tipificación Manual de Alta Precisión:**
   - Visualizador de páginas en miniatura con selector de intervalos.
   - Vista previa vectorial en HD con zoom interactivo inteligente al pasar el cursor.
   - Control de ciclos de radicación con soporte para deshacer pasos (`Ctrl+Z`).
2. **Autotipificación IA Avanzada:**
   - Motor OCR integrado asistido por `pymupdf`, `pytesseract` y `thefuzz` para la coincidencia difusa de nombres e identificaciones de pacientes.
   - Agrupación automática por afiliado y factura (detectando Actas CRC y Soportes OPF).
3. **Exportación Estructurada y Versátil:**
   - Creación automática de árboles de directorios organizados por `Fecha / EPS / Contrato`.
   - Generación de archivos nombrados bajo estandares institucionales (`CRC_900331412_FVCE<factura>.pdf`, etc.).
   - Opción de exportación plana o generación de reportes de sesión en texto.

---

## 🚀 Instalación y Ejecución (Entorno de Desarrollo)

1. Clona o descarga el repositorio en tu equipo local.
2. Crea y activa un entorno virtual de Python:
   ```bash
   python -m venv venv_tipificador
   # En Windows (Git Bash / CMD):
   source venv_tipificador/Scripts/activate