# tipificador_new.py — Versión Comercial Premium Definitiva (Genhospi)
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
import shutil
import tempfile
import pytesseract
from thefuzz import fuzz
from clasificador_ia import ClasificadorDocumentosIA
import cv2
import numpy as np
import pymupdf

# --- Apariencia global ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TipificadorFacturasApp(ctk.CTk):
    BG         = "#0F1115"
    SURFACE    = "#161922"
    SURFACE_2  = "#1F2331"
    BORDER     = "#2A2F3F"
    TEXT       = "#E6E9EF"
    MUTED      = "#8A93A6"
    ACCENT     = "#3B82F6"
    ACCENT_HO  = "#2563EB"
    SUCCESS    = "#10B981"
    SUCCESS_HO = "#059669"
    DANGER     = "#EF4444"
    WARN       = "#F59E0B"
    PAGE_BLOCK = "#3F1D1D"   
    PAGE_DONE  = "#1E3A8A"   

    def __init__(self):
        super().__init__()

        self.title("Genhospi - Sistema Inteligente de Tipificación y Auditoría v3.5")
        self.geometry("1360x880")
        self.minsize(1150, 750)
        self.configure(fg_color=self.BG)

        # --- Estado ---
        self.pdf_path = ""
        self.documento_pdf = None
        self.num_factura = tk.StringVar()
        self.modalidad = tk.IntVar(value=1)
        self.paso_actual = tk.IntVar(value=1)

        self.paginas_variables = []
        self.frames_items = []
        self.checkbuttons = []
        self.paginas_bloqueadas = []

        self.historial_ciclo = []
        self.registro_archivos = []
        self.registro_facturas = set()
        self.paquetes_detectados = []

        self._img_tk = None
        self.clasificador_ia = ClasificadorDocumentosIA()

        self._build_ui()
        self.bind('<Return>', lambda e: self.exportar_pdf())
        self.bind('<Control-z>', lambda e: self.deshacer_paso())

    def _build_ui(self):
        self.tabview = ctk.CTkTabview(
            self, 
            segmented_button_selected_color=self.ACCENT,
            segmented_button_selected_hover_color=self.ACCENT_HO,
            text_color=self.TEXT, 
            fg_color=self.BG
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=12)
        
        self.tab_manual = self.tabview.add("Tipificación Manual")
        self.tab_auto = self.tabview.add("Autotipificación IA Avanzada")
        
        self._build_ui_manual(self.tab_manual)
        self._build_ui_auto(self.tab_auto)

    def _build_ui_manual(self, parent):
        parent.grid_columnconfigure(0, weight=5)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)

        # ---------- Panel izquierdo: Vista Previa ----------
        preview_card = ctk.CTkFrame(parent, fg_color=self.SURFACE, corner_radius=16, border_width=1, border_color=self.BORDER)
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=(12, 6))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)

        lbl_titulo_prev = ctk.CTkLabel(preview_card, text="VISTA PREVIA HD (Doble clic para Zoom Interactivo)",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=self.ACCENT, anchor="w")
        lbl_titulo_prev.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))



        # ---------- Panel izquierdo: Vista Previa Interactiva Alta Calidad ----------
        preview_card = ctk.CTkFrame(parent, fg_color=self.SURFACE, corner_radius=16, border_width=1, border_color=self.BORDER)
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=(12, 6))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(preview_card, text="VISTA PREVIA HD — ZOOM AUTOMÁTICO AL PASAR EL MOUSE",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color=self.MUTED, anchor="w").grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        # Canvas para renderizado HD y Zoom por eventos de mouse
        self.canvas_preview = tk.Canvas(
            preview_card, bg=self.SURFACE_2, highlightthickness=0, bd=0
        )
        self.canvas_preview.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # Variables para control de Zoom y almacenamiento de imagen original
        self.imagen_pil_actual = None
        self._img_tk = None
        self.es_zoom = False

        # Eventos de Mouse para el Zoom
        self.canvas_preview.bind("<Enter>", lambda e: self.activar_zoom(True))
        self.canvas_preview.bind("<Leave>", lambda e: self.activar_zoom(False))
        self.canvas_preview.bind("<Motion>", self.actualizar_posicion_zoom)

        # ---------- Panel derecho: Controles y Selección Optimizada ----------
        side = ctk.CTkScrollableFrame(
            parent, fg_color=self.SURFACE, corner_radius=16, border_width=1, border_color=self.BORDER,
            scrollbar_button_color=self.SURFACE_2, scrollbar_button_hover_color=self.ACCENT
        )
        side.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=(12, 6))
        side.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            side, text="📂 Cargar PDF Lote", height=44, corner_radius=10,
            fg_color=self.ACCENT, hover_color=self.ACCENT_HO,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.cargar_pdf
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 12))

        # --- Sección: Factura con Estilo Moderno y Espaciado Amplio ---
        self._section_label(side, "Datos de Facturación", row=1)
        ctk.CTkLabel(side, text="Número de Factura (FVCE)", text_color=self.MUTED, anchor="w",
                     font=ctk.CTkFont(family="Segoe UI", size=11)).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 2))
        
        # Campo de factura con mayor tamaño de fuente y espaciado ampliado visualmente
        self.entry_factura = ctk.CTkEntry(
            side, textvariable=self.num_factura, height=45, corner_radius=10,
            fg_color=self.SURFACE_2, border_color=self.BORDER, border_width=1,
            text_color="#60A5FA", placeholder_text="Ej. 394174",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
        )
        self.entry_factura.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        self.entry_factura.bind("<Return>", lambda e: self.exportar_pdf())

        # --- Sección: Modalidad ---
        self._section_label(side, "Modalidad del Paquete", row=4)
        self._radio(side, "NOPBS  ·  2 archivos", self.modalidad, 1, row=5)
        self._radio(side, "Ambulatoria PBS  ·  3 archivos", self.modalidad, 2, row=6)

        # --- Sección: Paso ---
        self._section_label(side, "Paso de Tipificación Actual", row=7)
        self._radio(side, "1  ·  Acta de Entrega (CRC)", self.paso_actual, 1, row=8)
        self._radio(side, "2  ·  Fórmula / Soporte (OPF)", self.paso_actual, 2, row=9)
        self._radio(side, "3  ·  Autorización PBS", self.paso_actual, 3, row=10)

        # --- Sección: Páginas (Selector Rectangular Compacto sin Scroll Infinito Largo) ---
        self._section_label(side, "Seleccionar Páginas del Paquete", row=11)
        
        # Contenedor con altura máxima controlada (scroll interno compacto)
        self.paginas_container_frame = ctk.CTkFrame(side, fg_color=self.SURFACE_2, corner_radius=8, border_width=1, border_color=self.BORDER)
        self.paginas_container_frame.grid(row=12, column=0, sticky="ew", padx=6, pady=(0, 10))
        self.paginas_container_frame.grid_columnconfigure(0, weight=1)

        self.paginas_frame = ctk.CTkScrollableFrame(
            self.paginas_container_frame, fg_color="transparent", height=250,
            scrollbar_button_color=self.BORDER, scrollbar_button_hover_color=self.ACCENT
        )
        self.paginas_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.paginas_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # --- Botones de Acción ---
        ctk.CTkButton(
            side, text="⚡ Extraer y Tipificar Paquete", height=48, corner_radius=12,
            fg_color=self.SUCCESS, hover_color=self.SUCCESS_HO,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.exportar_pdf
        ).grid(row=13, column=0, sticky="ew", padx=6, pady=(8, 6))

        ctk.CTkButton(
            side, text="⟲ Deshacer Último Paso", height=38, corner_radius=10,
            fg_color=self.SURFACE_2, hover_color=self.BORDER, text_color=self.TEXT,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.deshacer_paso
        ).grid(row=14, column=0, sticky="ew", padx=6, pady=4)

        ctk.CTkButton(
            side, text="📄 Generar Reporte TXT de Sesión", height=40, corner_radius=10,
            fg_color=self.SURFACE_2, hover_color=self.BORDER, text_color=self.MUTED,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=self.generar_reporte_txt
        ).grid(row=15, column=0, sticky="ew", padx=6, pady=(4, 10))

        # Barra de estado inferior
        status_card = ctk.CTkFrame(parent, fg_color=self.SURFACE, corner_radius=12, border_width=1, border_color=self.BORDER)
        status_card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 6))
        status_card.grid_columnconfigure(0, weight=1)

        self.lbl_estado = ctk.CTkLabel(status_card, text="Sistema listo para iniciar.", text_color=self.MUTED, anchor="w",
                                       font=ctk.CTkFont(family="Segoe UI", size=12))
        self.lbl_estado.grid(row=0, column=0, sticky="ew", padx=16, pady=10)

    def _section_label(self, parent, text, row):
        ctk.CTkLabel(parent, text=text.upper(), text_color=self.MUTED, anchor="w",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")).grid(
            row=row, column=0, sticky="ew", padx=10, pady=(12, 4))

    def _radio(self, parent, text, var, value, row):
        ctk.CTkRadioButton(
            parent, text=text, variable=var, value=value, text_color=self.TEXT,
            fg_color=self.ACCENT, hover_color=self.ACCENT_HO, border_color=self.BORDER,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        ).grid(row=row, column=0, sticky="w", padx=10, pady=3)

    # -----------------------------------------------------------------
    # UI PESTAÑA AUTOMÁTICA (IA + Estructura de Carpetas)
    # -----------------------------------------------------------------
    def _build_ui_auto(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        ctrl_frame = ctk.CTkFrame(parent, fg_color=self.SURFACE, corner_radius=12)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkButton(ctrl_frame, text="1. Cargar PDF Multilote", fg_color=self.ACCENT, command=self.cargar_pdf_auto).pack(side="left", padx=10, pady=10)

        self.btn_escanear = ctk.CTkButton(
            ctrl_frame, text="2. 🤖 Ejecutar Autotipificación IA", fg_color=self.SUCCESS, 
            state="disabled", command=self.iniciar_escaneo_ia, text_color_disabled=self.TEXT
        )
        self.btn_escanear.pack(side="left", padx=10, pady=10)

        self.progress_bar = ctk.CTkProgressBar(ctrl_frame, width=220, progress_color=self.ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="right", padx=10, pady=10)

        self.txt_resultados = ctk.CTkTextbox(parent, fg_color=self.SURFACE_2, text_color=self.TEXT, font=("Consolas", 13))
        self.txt_resultados.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        exp_frame = ctk.CTkFrame(parent, fg_color=self.SURFACE, corner_radius=12)
        exp_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(exp_frame, text="Fecha (YYYY-MM-DD):", text_color=self.MUTED).pack(side="left", padx=5)
        self.entry_fecha = ctk.CTkEntry(exp_frame, width=110)
        self.entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha.pack(side="left", padx=5)

        ctk.CTkLabel(exp_frame, text="EPS:", text_color=self.MUTED).pack(side="left", padx=5)
        self.combo_eps = ctk.CTkComboBox(exp_frame, values=["SOS", "Sanitas", "Emssanar", "Asmet Salud"])
        self.combo_eps.pack(side="left", padx=5)

        ctk.CTkLabel(exp_frame, text="Contrato:", text_color=self.MUTED).pack(side="left", padx=5)
        self.combo_contrato = ctk.CTkComboBox(exp_frame, values=["EVENTO", "CAPITA", "NOPBS"])
        self.combo_contrato.pack(side="left", padx=5)

        self.btn_exportar_todo = ctk.CTkButton(exp_frame, text="3. 📁 Crear Estructura y Exportar", fg_color=self.ACCENT, state="disabled", command=self.exportar_auto)
        self.btn_exportar_todo.pack(side="right", padx=10)

        self.btn_exportar_plano = ctk.CTkButton(exp_frame, text="Exportar a Carpeta Plana", fg_color=self.SURFACE_2, state="disabled", command=self.exportar_a_carpeta_unica)
        self.btn_exportar_plano.pack(side="left", padx=10)

        self.lbl_estado_auto = ctk.CTkLabel(parent, text="Esperando archivo PDF para análisis automático...", text_color=self.MUTED)
        self.lbl_estado_auto.grid(row=3, column=0, sticky="w", padx=15, pady=5)

    def cargar_pdf_auto(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if not archivo: return
        self.pdf_path_auto = archivo
        self.btn_escanear.configure(state="normal")
        self.lbl_estado_auto.configure(text=f"Cargado: {os.path.basename(archivo)}", text_color=self.SUCCESS)
        self.txt_resultados.delete("1.0", "end")
        self.txt_resultados.insert("end", "Archivo cargado correctamente. Listo para procesar con IA.\n")
        self.paquetes_detectados = []

    def iniciar_escaneo_ia(self):
        if not hasattr(self, 'pdf_path_auto') or not self.pdf_path_auto: return
        self.btn_escanear.configure(state="disabled")
        self.progress_bar.set(0)
        self.txt_resultados.delete("1.0", "end")
        self.txt_resultados.insert("end", "Iniciando escaneo inteligente de páginas y clasificación OCR...\n")
        threading.Thread(target=self._procesar_ia_background, daemon=True).start()

    def _procesar_ia_background(self):
        try:
            doc = pymupdf.open(self.pdf_path_auto)
            total_paginas = len(doc)
            paginas_info = []

            for i in range(total_paginas):
                page = doc.load_page(i)
                # Extracción nativa rápida
                texto_nativo = page.get_text("text")
                # Renderizado solo para el fallback OCR o para la previsualización
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
                datos_ia = self.clasificador_ia.analizar_pagina(img, texto_nativo=texto_nativo)
                
                paginas_info.append({
                    'pagina': i,
                    'factura': datos_ia.get('numero_factura'),
                    'paciente_nombre': datos_ia.get('paciente'),
                    'paciente_id': datos_ia.get('identificacion'),
                    'es_crc': datos_ia.get('tipo') == 'CRC',
                    'es_opf': datos_ia.get('tipo') == 'OPF',
                })
                self.after(0, lambda p=(i + 1) / total_paginas: self.progress_bar.set(p))

            doc.close()
            self.paquetes_detectados = self._agrupar_paquetes_por_afiliado(paginas_info)
            self.after(0, self._mostrar_resultados_ia)
        except Exception as e:
            self.after(0, lambda: self.lbl_estado_auto.configure(text=f"Error crítico en IA: {e}", text_color=self.DANGER))
            self.after(0, lambda: self.btn_escanear.configure(state="normal"))

    def _agrupar_paquetes_por_afiliado(self, paginas_info):
        grupos = []
        for p in paginas_info:
            id_pac = p['paciente_id']
            nom_pac = self._normalizar_nombre(p['paciente_nombre'])
            factura = p['factura']

            mejor_grupo = None
            mejor_puntaje = 0

            for g in grupos:
                puntaje = 0
                # El ID de paciente es el discriminante más fuerte
                if id_pac and g['paciente_id'] == id_pac:
                    puntaje += 20
                # La factura también es fuerte, pero solo si existe
                if factura and g['factura'] == factura:
                    puntaje += 15
                # El nombre solo suma si hay coincidencia muy alta (>= 90)
                if nom_pac and g['paciente_nombre_norm']:
                    similitud = fuzz.token_set_ratio(nom_pac, g['paciente_nombre_norm'])
                    if similitud >= 90:
                        puntaje += 8

                # Umbral más alto y estricto (>= 15 para evitar agrupar por debilidad)
                if puntaje >= 15 and puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor_grupo = g

            if mejor_grupo:
                if factura and not mejor_grupo['factura']: 
                    mejor_grupo['factura'] = factura
                if id_pac and not mejor_grupo['paciente_id']: 
                    mejor_grupo['paciente_id'] = id_pac
                if p['paciente_nombre'] and mejor_grupo['paciente'] == "Desconocido": 
                    mejor_grupo['paciente'] = p['paciente_nombre']
                grupo = mejor_grupo
            else:
                grupo = {
                    'factura': factura,
                    'paciente': p['paciente_nombre'] or "Desconocido",
                    'paciente_id': id_pac,
                    'paciente_nombre_norm': nom_pac,
                    'crc': [], 'opf': [], 'no_clasificados': []
                }
                grupos.append(grupo)

            if p['es_crc']: 
                grupo['crc'].append(p['pagina'] + 1)
            elif p['es_opf']: 
                grupo['opf'].append(p['pagina'] + 1)
            else: 
                grupo['no_clasificados'].append(p['pagina'] + 1)

        return grupos

    def _normalizar_nombre(self, nombre):
        if not nombre: return None
        import unicodedata
        n = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('utf-8').upper()
        return re.sub(r'[^A-Z\s]', '', n).strip()

    def _mostrar_resultados_ia(self):
        self.txt_resultados.delete("1.0", "end")
        if not self.paquetes_detectados:
            self.txt_resultados.insert("end", "No se detectaron paquetes válidos.\n")
            return

        for idx, paquete in enumerate(self.paquetes_detectados, 1):
            self.txt_resultados.insert("end", f"[{idx}] Paciente: {paquete['paciente']} (ID: {paquete['paciente_id']})\n")
            self.txt_resultados.insert("end", f"    Factura Detectada: FVCE{paquete['factura'] if paquete['factura'] else 'NO ASIGNADA'}\n")
            self.txt_resultados.insert("end", f"    - CRC (Acta): Páginas {paquete['crc']}\n")
            self.txt_resultados.insert("end", f"    - OPF (Soportes): Páginas {paquete['opf']}\n")
            if paquete['no_clasificados']:
                self.txt_resultados.insert("end", f"    ⚠️ Sin clasificar: Páginas {paquete['no_clasificados']}\n")
            self.txt_resultados.insert("end", "-"*60 + "\n")

        self.btn_exportar_todo.configure(state="normal")
        self.btn_exportar_plano.configure(state="normal")
        self.lbl_estado_auto.configure(text="¡Autotipificación completada con éxito!", text_color=self.SUCCESS)
        self.btn_escanear.configure(state="normal")

    def _es_factura_valida(self, factura):
        if not factura:
            return False
        # Una factura FVCE típica tiene 6-8 dígitos
        return bool(re.fullmatch(r'\d{6,8}', str(factura)))

    def exportar_auto(self):
        if not self.paquetes_detectados: return
        fecha, eps, contrato = self.entry_fecha.get().strip(), self.combo_eps.get().strip(), self.combo_contrato.get().strip()
        if not fecha or not eps or not contrato:
            messagebox.showerror("Campos incompletos", "Complete Fecha, EPS y Contrato.")
            return

        base_dir = os.path.dirname(self.pdf_path_auto)
        ruta_destino = os.path.join(base_dir, fecha, eps, contrato)
        os.makedirs(ruta_destino, exist_ok=True)

        doc_origen = pymupdf.open(self.pdf_path_auto)
        guardados = 0
        try:
            for paquete in self.paquetes_detectados:
                factura = paquete.get('factura')
                
                # Validación de factura inválida
                if not self._es_factura_valida(factura):
                    print(f"⚠️ Grupo omitido: factura inválida '{factura}'")
                    continue

                if paquete.get('crc'):
                    nombre_crc = f"CRC_900331412_FVCE{factura}.pdf"
                    self._extraer_paginas_pdf(doc_origen, paquete['crc'], os.path.join(ruta_destino, nombre_crc))
                    guardados += 1
                if paquete.get('opf'):
                    nombre_opf = f"OPF_900331412_FVCE{factura}.pdf"
                    self._extraer_paginas_pdf(doc_origen, paquete['opf'], os.path.join(ruta_destino, nombre_opf))
                    guardados += 1

            self.lbl_estado_auto.configure(text=f"✅ {guardados} archivos estructurados creados correctamente.", text_color=self.SUCCESS)
            self._abrir_carpeta(ruta_destino)
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar estructura: {e}")
        finally:
            doc_origen.close()

    def exportar_a_carpeta_unica(self):
        if not self.paquetes_detectados: return
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not carpeta: return

        doc_origen = pymupdf.open(self.pdf_path_auto)
        try:
            for paquete in self.paquetes_detectados:
                factura = paquete.get('factura')
                
                # Validación de factura inválida
                if not self._es_factura_valida(factura):
                    print(f"⚠️ Grupo omitido: factura inválida '{factura}'")
                    continue

                if paquete.get('crc'):
                    self._extraer_paginas_pdf(doc_origen, paquete['crc'], os.path.join(carpeta, f"CRC_900331412_FVCE{factura}.pdf"))
                if paquete.get('opf'):
                    self._extraer_paginas_pdf(doc_origen, paquete['opf'], os.path.join(carpeta, f"OPF_900331412_FVCE{factura}.pdf"))
                    
            self.lbl_estado_auto.configure(text=f"✅ Exportado a plano en: {carpeta}", text_color=self.SUCCESS)
            self._abrir_carpeta(carpeta)
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar: {e}")
        finally:
            doc_origen.close()

    def _extraer_paginas_pdf(self, doc_origen, paginas, destino):
        doc_nuevo = pymupdf.open()
        for p in paginas:
            doc_nuevo.insert_pdf(doc_origen, from_page=p-1, to_page=p-1)
        doc_nuevo.save(destino, garbage=4, deflate=True, clean=True)
        doc_nuevo.close()

    # -----------------------------------------------------------------
    # MÉTODOS DE LA PESTAÑA MANUAL Y UI HELPERS
    # -----------------------------------------------------------------
    def cargar_pdf(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos PDF", "*.pdf")])
        if not archivo: return
        self.pdf_path = archivo
        if self.documento_pdf: self.documento_pdf.close()

        try:
            self.documento_pdf = pymupdf.open(archivo)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el PDF:\n{e}")
            return

        for w in self.paginas_frame.winfo_children(): w.destroy()
        self.paginas_variables, self.frames_items, self.checkbuttons, self.paginas_bloqueadas, self.historial_ciclo = [], [], [], [], []
        self.paso_actual.set(1)
        self.num_factura.set("")
        self.set_status(f"PDF cargado con éxito ({len(self.documento_pdf)} páginas)")

        columnas = 3  # 2 columnas para un diseño rectangular estilizado
        for i in range(len(self.documento_pdf)):
            fila, col = i // columnas, i % columnas

            # Tarjeta rectangular elegante para cada página
            item = ctk.CTkFrame(self.paginas_frame, fg_color=self.SURFACE_2, corner_radius=8, border_width=1, border_color=self.BORDER)
            item.grid(row=fila, column=col, padx=4, pady=4, sticky="ew")
            item.grid_columnconfigure(0, weight=1)

            ctk.CTkButton(
                item, text=f"Página {i+1}", height=26, corner_radius=6,
                fg_color=self.ACCENT, hover_color=self.ACCENT_HO,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda n=i: self.mostrar_vista_previa(n)
            ).grid(row=0, column=0, padx=4, pady=(4, 2), sticky="ew")

            var = tk.BooleanVar()
            # Checkbox rectangular estilizado
            chk = ctk.CTkCheckBox(
                item, text=f"Sel. Pág {i+1}", variable=var, width=100, height=22,
                checkbox_width=24, checkbox_height=16, corner_radius=4,
                fg_color=self.ACCENT, hover_color=self.ACCENT_HO, border_color=self.BORDER,
                font=ctk.CTkFont(family="Segoe UI", size=10)
            )
            chk.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="w")

            self.paginas_variables.append(var)
            self.frames_items.append(item)
            self.checkbuttons.append(chk)

        if len(self.documento_pdf) > 0: self.mostrar_vista_previa(0)

    def mostrar_vista_previa(self, num_pagina):
        if not self.documento_pdf: return
        try:
            # Renderizado vectorial de alta calidad (DPI 200 para máxima nitidez sin pérdida)
            pagina = self.documento_pdf.load_page(num_pagina)
            pix = pagina.get_pixmap(dpi=200, colorspace=pymupdf.csRGB)
            self.imagen_pil_actual = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            self.renderizar_imagen_canvas()
        except Exception as e:
            self.set_status(f"Error al previsualizar HD: {e}", self.DANGER)

    def renderizar_imagen_canvas(self, factor_zoom=1.0, centro_x=None, centro_y=None):
        if self.imagen_pil_actual is None: return
        
        self.update_idletasks()
        canvas_w = max(self.canvas_preview.winfo_width(), 700)
        canvas_h = max(self.canvas_preview.winfo_height(), 550)

        img_w, img_h = self.imagen_pil_actual.size
        
        # Escala base manteniendo proporción original exacta (sin recortes deformes)
        escala = min(canvas_w / img_w, canvas_h / img_h)
        nuevo_w = int(img_w * escala * factor_zoom)
        nuevo_h = int(img_h * escala * factor_zoom)

        img_redimensionada = self.imagen_pil_actual.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        
        self._img_tk = ImageTk.PhotoImage(img_redimensionada)
        self.canvas_preview.delete("all")
        
        # Centrar imagen en el canvas
        pos_x = (canvas_w - nuevo_w) // 2 if centro_x is None else centro_x
        pos_y = (canvas_h - nuevo_h) // 2 if centro_y is None else centro_y
        
        self.canvas_preview.create_image(max(0, pos_x), max(0, pos_y), anchor="nw", image=self._img_tk)

    def activar_zoom(self, activar):
        self.es_zoom = activar
        if not activar and self.imagen_pil_actual:
            self.renderizar_imagen_canvas(factor_zoom=1.0)

    def actualizar_posicion_zoom(self, event):
        if not self.es_zoom or self.imagen_pil_actual is None: return
        # Zoom leve del 1.4x al pasar el mouse por encima
        canvas_w = self.canvas_preview.winfo_width()
        canvas_h = self.canvas_preview.winfo_height()
        
        # Coordenadas relativas del mouse para enfocar el zoom donde apunta el auditor
        factor = 1.6
        img_w, img_h = self.imagen_pil_actual.size
        escala = min(canvas_w / img_w, canvas_h / img_h) * factor
        
        nuevo_w = int(img_w * (escala / factor) * factor)
        nuevo_h = int(img_h * (escala / factor) * factor)
        
        # Desplazamiento proporcional al cursor
        offset_x = int((event.x / canvas_w) * (canvas_w - nuevo_w))
        offset_y = int((event.y / canvas_h) * (canvas_h - nuevo_h))
        
        img_redimensionada = self.imagen_pil_actual.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        self._img_tk = ImageTk.PhotoImage(img_redimensionada)
        
        self.canvas_preview.delete("all")
        self.canvas_preview.create_image(offset_x, offset_y, anchor="nw", image=self._img_tk)



    def set_status(self, text, color=None):
        self.lbl_estado.configure(text=text, text_color=color or self.MUTED)

    def _abrir_carpeta(self, ruta):
        try:
            if sys.platform == "win32": os.startfile(ruta)
            elif sys.platform == "darwin": subprocess.Popen(["open", ruta])
            else: subprocess.Popen(["xdg-open", ruta])
        except Exception: pass

    def deshacer_paso(self):
        if not self.historial_ciclo:
            self.set_status("No hay acciones recientes para deshacer.", self.WARN)
            return
        u = self.historial_ciclo.pop()
        if os.path.exists(u['ruta_archivo']):
            try: os.remove(u['ruta_archivo'])
            except Exception: pass

        if u['nombre_archivo'] in self.registro_archivos: self.registro_archivos.remove(u['nombre_archivo'])
        self.paso_actual.set(u['paso'])
        for p in u['paginas_usadas']:
            if p in self.paginas_bloqueadas: self.paginas_bloqueadas.remove(p)
            self.frames_items[p].configure(fg_color=self.SURFACE_2)
            self.checkbuttons[p].configure(state="normal")
            self.paginas_variables[p].set(True)
        self.set_status(f"Paso {u['paso']} deshecho correctamente.", self.WARN)

    def terminar_ciclo(self, ultima_pagina):
        self.num_factura.set("")
        self.paso_actual.set(1)
        self.historial_ciclo = []
        for i in range(len(self.paginas_variables)):
            self.paginas_variables[i].set(False)
            self.frames_items[i].configure(fg_color=self.SURFACE_2)
            self.checkbuttons[i].configure(state="normal")
        self.paginas_bloqueadas = []
        self.frames_items[ultima_pagina].configure(fg_color=self.PAGE_DONE)
        carpeta = os.path.dirname(self.pdf_path) if self.pdf_path else os.getcwd()
        self.set_status(f"¡Ciclo completado! Paquete guardado en: {carpeta}", self.SUCCESS)
        self._abrir_carpeta(carpeta)

    def generar_reporte_txt(self):
        if not self.registro_archivos:
            messagebox.showinfo("Reporte", "No hay archivos tipificados en esta sesión.")
            return
        ruta = os.path.join(os.path.dirname(self.pdf_path), "Reporte_Tipificacion_Genhospi.txt")
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("=== REPORTE DE TIPIFICACIÓN GENHOSPI ===\n\n")
                for a in self.registro_archivos: f.write(f"{a}.pdf\n")
            messagebox.showinfo("Reporte Generado", f"Guardado en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el reporte: {e}")

    def exportar_pdf(self):
        factura_bruta = self.num_factura.get().strip()
        factura = re.sub(r'[<>:"/\\|?*]', '', factura_bruta)
        if not factura:
            self.set_status("Debe ingresar un número de factura válido.", self.DANGER)
            self.entry_factura.configure(border_color=self.DANGER)
            self.after(1200, lambda: self.entry_factura.configure(border_color=self.BORDER))
            return

        modalidad, paso = self.modalidad.get(), self.paso_actual.get()
        if not self.pdf_path:
            self.set_status("Cargue un PDF primero.", self.DANGER)
            return

        paginas_a_extraer = [i for i, v in enumerate(self.paginas_variables) if v.get()]
        if not paginas_a_extraer:
            self.set_status("Seleccione al menos una página.", self.DANGER)
            return

        nombre_salida = f"CRC_900331412_FVCE{factura}" if paso == 1 else (f"OPF_900331412_FVCE{factura}" if paso == 2 else f"CRC_900331412_FVCE{factura}-1")
        ruta = os.path.join(os.path.dirname(self.pdf_path), f"{nombre_salida}.pdf")

        try:
            doc = pymupdf.open()
            for p in paginas_a_extraer: doc.insert_pdf(self.documento_pdf, from_page=p, to_page=p)
            doc.save(ruta, garbage=4, deflate=True, clean=True)
            doc.close()

            self.registro_archivos.append(nombre_salida)
            self.historial_ciclo.append({'paso': paso, 'paginas_usadas': paginas_a_extraer, 'ruta_archivo': ruta, 'nombre_archivo': nombre_salida})
            ultima = max(paginas_a_extraer)

            if paso == 1:
                for p in paginas_a_extraer:
                    self.paginas_bloqueadas.append(p)
                    self.paginas_variables[p].set(False)
                    self.frames_items[p].configure(fg_color=self.PAGE_BLOCK)
                    self.checkbuttons[p].configure(state="disabled")
                self.paso_actual.set(2)
                self.set_status("Acta CRC guardada. Seleccione la Fórmula/Soporte (OPF).", self.ACCENT)
            elif paso == 2:
                if modalidad == 1: self.terminar_ciclo(ultima)
                else:
                    for p in paginas_a_extraer:
                        self.paginas_bloqueadas.append(p)
                        self.paginas_variables[p].set(False)
                        self.frames_items[p].configure(fg_color=self.PAGE_BLOCK)
                        self.checkbuttons[p].configure(state="disabled")
                    self.paso_actual.set(3)
                    self.set_status("Soporte guardado. Seleccione Autorización PBS.", self.ACCENT)
            elif paso == 3:
                self.terminar_ciclo(ultima)
        except Exception as e:
            self.set_status(f"Error al exportar: {e}", self.DANGER)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = TipificadorFacturasApp()
    app.mainloop()