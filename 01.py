import streamlit as st
import pandas as pd
import tempfile
import os
from typing import List, Dict
from datetime import datetime
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import pytesseract
from PIL import Image
import base64
import json

# Configuración inicial
st.set_page_config(page_title="Declaración Modelo 130 Mejorada", layout="wide")

st.title("🧾 Declaración automática Modelo 130 (versión mejorada)")

# -- Funciones auxiliares --

def ocr_extract_text_from_image(image_path: str) -> str:
    """Extrae texto usando OCR de una imagen."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='spa')
        return text
    except Exception as e:
        st.error(f"Error en OCR: {e}")
        return ""

def parse_factura_text(text: str) -> Dict:
    """
    Procesa texto OCR para extraer datos clave aproximados.
    NOTA: Ejemplo simple, se debe ajustar para casos reales con expresiones regulares más complejas.
    """
    datos = {"fecha": None, "nif": None, "base": None, "iva": None, "retencion": 0.0}
    lines = text.split("\n")
    for line in lines:
        line_low = line.lower()
        if "fecha" in line_low:
            # Extraer fecha (simplificado)
            try:
                posibles_fechas = [word for word in line.split() if any(c.isdigit() for c in word)]
                for pf in posibles_fechas:
                    try:
                        fecha = datetime.strptime(pf, "%d/%m/%Y")
                        datos["fecha"] = fecha.strftime("%Y-%m-%d")
                        break
                    except:
                        continue
            except:
                pass
        if "nif" in line_low or "cif" in line_low:
            partes = line.split()
            for p in partes:
                if len(p) >= 9 and any(c.isdigit() for c in p):
                    datos["nif"] = p.strip()
                    break
        if "base imponible" in line_low:
            try:
                base = [float(s.replace("€","").replace(",",".")) for s in line.split() if s.replace(",","").replace(".","").isdigit() or s.replace(",","").replace(".","").replace("€","").isdigit()]
                if base:
                    datos["base"] = base[0]
            except:
                pass
        if "iva" in line_low:
            try:
                iva = [float(s.replace("€","").replace(",",".")) for s in line.split() if s.replace(",","").replace(".","").isdigit()]
                if iva:
                    datos["iva"] = iva[0]
            except:
                pass
        if "retención" in line_low or "retencion" in line_low:
            try:
                ret = [float(s.replace("€","").replace(",",".")) for s in line.split() if s.replace(",","").replace(".","").isdigit()]
                if ret:
                    datos["retencion"] = ret[0]
            except:
                pass
    return datos

def to_csv_download_link(df, filename="datos.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Descargar CSV</a>'
    return href

def save_session_data(data: Dict, filename="session_data.json"):
    with open(filename, "w") as f:
        json.dump(data, f)

def load_session_data(filename="session_data.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None

# -- Inicio interfaz --

# Paso 1: Datos fiscales
with st.expander("Paso 1 – Datos personales y fiscales", expanded=True):
    nif = st.text_input("NIF/NIE", max_chars=15)
    nombre = st.text_input("Nombre completo o razón social")
    regimen = st.selectbox("Régimen fiscal", ["Estimación directa simplificada", "Estimación directa normal"])
    iae = st.text_input("Código de actividad económica (IAE)")
    ejercicio = st.selectbox("Ejercicio fiscal", [str(y) for y in range(2020, 2026)], index=5)
    trimestre = st.selectbox("Trimestre", ["1", "2", "3", "4"])

# Paso 2: Subida de facturas y extracción de datos
st.markdown("### Paso 2 – Subida de facturas (PDF, imágenes o CSV)")

facturas = []

uploaded_files = st.file_uploader("Sube aquí tus facturas (pueden ser múltiples, PDF, JPG, PNG o CSV)", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        ext = uploaded_file.name.split(".")[-1].lower()
        if ext in ["png", "jpg", "jpeg", "pdf"]:
            # Guardar temporalmente para OCR
            with tempfile.NamedTemporaryFile(delete=False, suffix="."+ext) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Extraer texto por OCR
            texto = ocr_extract_text_from_image(tmp_path)
            datos = parse_factura_text(texto)
            datos["archivo"] = uploaded_file.name
            facturas.append(datos)

            os.unlink(tmp_path)

        elif ext == "csv":
            try:
                df = pd.read_csv(uploaded_file)
                for _, row in df.iterrows():
                    factura = {
                        "fecha": row.get("fecha", None),
                        "nif": row.get("nif", None),
                        "base": float(row.get("importe_sin_iva", 0)),
                        "iva": float(row.get("iva", 0)),
                        "retencion": float(row.get("retencion", 0)) if "retencion" in row else 0,
                        "archivo": uploaded_file.name,
                    }
                    facturas.append(factura)
            except Exception as e:
                st.error(f"Error leyendo CSV {uploaded_file.name}: {e}")
        else:
            st.warning(f"Archivo {uploaded_file.name} no soportado para extracción automática.")

# Mostrar facturas procesadas para revisión y edición
if facturas:
    st.markdown("#### Facturas detectadas (puede editar valores si es necesario):")

    # Convertir a dataframe para edición rápida
    df_facturas = pd.DataFrame(facturas)

    edited_df = st.data_editor(df_facturas, num_rows="dynamic")

    # Cálculo por tipo de factura
    ingresos = edited_df["base"].sum()
    retenciones_total = edited_df["retencion"].sum()

    # Filtrar gastos deducibles (se podría mejorar con clasificación)
    # Para ejemplo simple: se asume que los gastos están en CSV separado, o se añade campo 'tipo'
    # Aquí suponemos que todas las facturas subidas son ingresos
    gastos = 0.0

else:
    st.info("No se han subido facturas o no se han extraído datos.")

# Paso 3: Gastos manuales y adicionales
st.markdown("### Paso 3 – Gastos deducibles adicionales o no digitalizados")
gastos_manual = st.number_input("Introducir gastos deducibles adicionales", min_value=0.0, step=50.0, format="%.2f")

# Paso 4: Retenciones y pagos fraccionados
st.markdown("### Paso 4 – Retenciones y pagos fraccionados")
retenciones_input = st.number_input("IRPF retenido por clientes (manual o corregido)", min_value=0.0, step=50.0, format="%.2f", value=retenciones_total if facturas else 0.0)
pagos_previos = st.number_input("Pagos fraccionados ya realizados en el año", min_value=0.0, step=50.0, format="%.2f")

# Paso 5: Cálculo y visualización resultados
if st.button("Calcular declaración"):
    rendimiento_neto = ingresos - (gastos + gastos_manual)
    porcentaje_fraccionado = 0.20 if regimen == "Estimación directa simplificada" else 0.20  # Se puede ajustar para normal
    pago_fraccionado = max(0, rendimiento_neto * porcentaje_fraccionado)

    resultado_final = pago_fraccionado - retenciones_input - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado de la declaración")

    st.write(f"**Ingresos totales:** {ingresos:.2f} €")
    st.write(f"**Gastos totales:** {(gastos + gastos_manual):.2f} €")
    st.write(f"**Rendimiento neto (Ingresos - Gastos):** {rendimiento_neto:.2f} €")
    st.write(f"**Pago fraccionado ({int(porcentaje_fraccionado*100)} % sobre rendimiento):** {pago_fraccionado:.2f} €")
    st.write(f"**IRPF retenido por clientes:** {retenciones_input:.2f} €")
    st.write(f"**Pagos fraccionados realizados anteriormente:** {pagos_previos:.2f} €")

    if resultado_final >= 0:
        st.success(f"**Importe a ingresar:** {resultado_final:.2f} €")
    else:
        st.info(f"**Importe a compensar (a favor):** {abs(resultado_final):.2f} €")

    # Permitir descarga resumen
    resumen = {
        "NIF": nif,
        "Nombre": nombre,
        "Ejercicio": ejercicio,
        "Trimestre": trimestre,
        "Régimen": regimen,
        "Ingresos": ingresos,
        "Gastos": gastos + gastos_manual,
        "Rendimiento Neto": rendimiento_neto,
        "Pago fraccionado": pago_fraccionado,
        "Retenciones": retenciones_input,
        "Pagos previos": pagos_previos,
        "Resultado final": resultado_final,
    }

    df_resumen = pd.DataFrame([resumen])

    st.markdown(to_csv_download_link(df_resumen, filename="resumen_modelo_130.csv"), unsafe_allow_html=True)

# Paso 6: Histórico (guardado en sesión simple)

if 'historial' not in st.session_state:
    st.session_state.historial = []

if st.button("Guardar resultado en historial"):
    if 'resultado_final' in locals():
        st.session_state.historial.append(resumen)
        st.success("Resultado guardado en historial.")

if st.session_state.historial:
    st.markdown("---")
    st.subheader("📚 Historial de declaraciones calculadas")
    df_historial = pd.DataFrame(st.session_state.historial)
    st.dataframe(df_historial)

    # Opción para descargar todo el histórico
    st.markdown(to_csv_download_link(df_historial, filename="historial_modelo_130.csv"), unsafe_allow_html=True)

# Paso 7: Comunicación (chat simple)

st.markdown("---")
st.subheader("📩 Consulta a tu asesor")

if 'chat' not in st.session_state:
    st.session_state.chat = []

mensaje = st.text_area("Escribe tu consulta o comentario")

if st.button("Enviar consulta"):
    if mensaje.strip() != "":
        st.session_state.chat.append({"mensaje": mensaje, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        st.success("Consulta enviada al asesor.")
    else:
        st.warning("El mensaje está vacío.")

if st.session_state.chat:
    for i, c in enumerate(reversed(st.session_state.chat[-5:])):  # Mostrar últimos 5 mensajes
        st.write(f"[{c['timestamp']}] Cliente: {c['mensaje']}")

# Notas finales
st.markdown("""
---
### Notas importantes  
- Esta herramienta es orientativa y no sustituye el asesoramiento profesional personalizado.  
- El reconocimiento de facturas mediante OCR es básico y puede requerir revisión manual.  
- Asegúrese de revisar y corregir cualquier dato extraído automáticamente.  
- Los cálculos se realizan bajo supuestos simplificados; consulte siempre con un asesor fiscal.  
""")



