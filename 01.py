import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import re
import io

st.set_page_config(page_title="Declaración Modelo 130", layout="centered")

st.title("🧾 Declaración automática Modelo 130")
st.subheader("Paso 1 – Tus datos fiscales y económicos")

# -- Datos fiscales básicos --
with st.expander("Datos personales y fiscales"):
    nif = st.text_input("NIF/NIE")
    nombre = st.text_input("Nombre completo o razón social")
    regimen = st.selectbox("Régimen fiscal", options=["Estimación directa simplificada", "Estimación directa normal"])
    iae = st.text_input("Código actividad económica (IAE)")
    ejercicio = st.selectbox("Ejercicio fiscal", options=[str(y) for y in range(2020, 2026)], index=5)
    trimestre = st.selectbox("Trimestre", options=["1", "2", "3", "4"])

st.markdown("### Paso 2 – Ingresos y gastos acumulados")
st.markdown("**Puedes introducir los datos manualmente, subir CSV/Excel o usar imágenes/PDFs**")

# ========== INGRESOS ==========

ingresos_totales = 0.0

st.markdown("#### 🧾 Ingresos")

# CSV
if st.checkbox("Subir archivo CSV con facturas emitidas (ingresos)"):
    ingresos_csv = st.file_uploader("Archivo CSV ingresos", type=["csv"])
    if ingresos_csv:
        df_ingresos = pd.read_csv(ingresos_csv)
        if "importe_sin_iva" in df_ingresos.columns:
            ingresos_totales += df_ingresos["importe_sin_iva"].sum()
            st.success(f"Total ingresos por CSV: {ingresos_totales:.2f} €")
        else:
            st.error("El CSV debe tener una columna 'importe_sin_iva'")

# Imagen/PDF con OCR
if st.checkbox("Subir imágenes o PDFs de facturas (ingresos)"):
    ingresos_ocr = st.file_uploader("Imágenes o PDFs", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)
    ocr_ingresos_total = 0.0
    for archivo in ingresos_ocr:
        if archivo.type == "application/pdf":
            paginas = convert_from_bytes(archivo.read())
            for pagina in paginas:
                texto = pytesseract.image_to_string(pagina)
                cantidades = re.findall(r"\d+[.,]?\d{2}", texto)
                for c in cantidades:
                    try:
                        importe = float(c.replace(",", "."))
                        if importe > 0:
                            ocr_ingresos_total += importe
                    except:
                        continue
        elif archivo.type.startswith("image/"):
            imagen = Image.open(archivo)
            texto = pytesseract.image_to_string(imagen)
            cantidades = re.findall(r"\d+[.,]?\d{2}", texto)
            for c in cantidades:
                try:
                    importe = float(c.replace(",", "."))
                    if importe > 0:
                        ocr_ingresos_total += importe
                except:
                    continue
    if ocr_ingresos_total > 0:
        ingresos_totales += ocr_ingresos_total
        st.success(f"Total ingresos detectados por OCR: {ocr_ingresos_total:.2f} €")
        st.info(f"Total ingresos sumado: {ingresos_totales:.2f} €")

# Manual
if ingresos_totales == 0:
    ingresos_totales = st.number_input("Ingresos acumulados manualmente (sin IVA)", min_value=0.0, step=100.0, format="%.2f")

# ========== GASTOS ==========

gastos_totales = 0.0

st.markdown("#### 💸 Gastos deducibles")

# CSV
if st.checkbox("Subir archivo CSV con facturas recibidas (gastos)"):
    gastos_csv = st.file_uploader("Archivo CSV gastos", type=["csv"])
    if gastos_csv:
        df_gastos = pd.read_csv(gastos_csv)
        if "importe" in df_gastos.columns:
            gastos_totales += df_gastos["importe"].sum()
            st.success(f"Total gastos por CSV: {gastos_totales:.2f} €")
        else:
            st.error("El CSV debe tener una columna 'importe'")

# Imagen/PDF con OCR
if st.checkbox("Subir imágenes o PDFs de facturas (gastos)"):
    gastos_ocr = st.file_uploader("Imágenes o PDFs", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)
    ocr_gastos_total = 0.0
    for archivo in gastos_ocr:
        if archivo.type == "application/pdf":
            paginas = convert_from_bytes(archivo.read())
            for pagina in paginas:
                texto = pytesseract.image_to_string(pagina)
                cantidades = re.findall(r"\d+[.,]?\d{2}", texto)
                for c in cantidades:
                    try:
                        importe = float(c.replace(",", "."))
                        if importe > 0:
                            ocr_gastos_total += importe
                    except:
                        continue
        elif archivo.type.startswith("image/"):
            imagen = Image.open(archivo)
            texto = pytesseract.image_to_string(imagen)
            cantidades = re.findall(r"\d+[.,]?\d{2}", texto)
            for c in cantidades:
                try:
                    importe = float(c.replace(",", "."))
                    if importe > 0:
                        ocr_gastos_total += importe
                except:
                    continue
    if ocr_gastos_total > 0:
        gastos_totales += ocr_gastos_total
        st.success(f"Total gastos detectados por OCR: {ocr_gastos_total:.2f} €")
        st.info(f"Total gastos sumado: {gastos_totales:.2f} €")

# Manual
if gastos_totales == 0:
    gastos_totales = st.number_input("Gastos deducibles manualmente", min_value=0.0, step=100.0, format="%.2f")

# ========== RETENCIONES Y PAGOS ==========

retenciones = st.number_input("IRPF retenido por clientes", min_value=0.0, step=50.0, format="%.2f")
pagos_previos = st.number_input("Pagos fraccionados realizados este año", min_value=0.0, step=50.0, format="%.2f")

if ingresos_totales < gastos_totales:
    st.warning("⚠️ Los gastos superan a los ingresos. Revíselo si no corresponde a su situación.")

# ========== CÁLCULO FINAL ==========

if st.button("Calcular declaración"):
    rendimiento = ingresos_totales - gastos_totales
    fraccionado = max(0, rendimiento * 0.20)
    resultado = fraccionado - retenciones - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado del trimestre")
    st.write(f"**Rendimiento neto (Ingresos - Gastos):** {rendimiento:.2f} €")
    st.write(f"**20 % del rendimiento (Pago fraccionado):** {fraccionado:.2f} €")
    st.write(f"**Retenciones soportadas:** {retenciones:.2f} €")
    st.write(f"**Pagos fraccionados previos:** {pagos_previos:.2f} €")

    if resultado >= 0:
        st.success(f"**Importe a ingresar:** {resultado:.2f} €")
    else:
        st.info(f"**Importe a compensar:** {abs(resultado):.2f} €")

    st.markdown("""
    ---
    **Notas:**  
    - El rendimiento neto se calcula como ingresos menos gastos deducibles.  
    - El pago fraccionado es el 20 % de ese rendimiento.  
    - Se descuentan retenciones y pagos previos realizados.  
    - Si el resultado es negativo, puede compensarse en trimestres siguientes.  
    """)

