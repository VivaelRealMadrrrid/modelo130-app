import streamlit as st
import pandas as pd
import base64
from datetime import datetime

st.set_page_config(page_title="Declaración Modelo 130 Simplificada", layout="wide")

st.title("🧾 Declaración automática Modelo 130 (versión simplificada)")

# Paso 1: Datos fiscales
with st.expander("Paso 1 – Datos personales y fiscales", expanded=True):
    nif = st.text_input("NIF/NIE", max_chars=15)
    nombre = st.text_input("Nombre completo o razón social")
    regimen = st.selectbox("Régimen fiscal", ["Estimación directa simplificada", "Estimación directa normal"])
    iae = st.text_input("Código de actividad económica (IAE)")
    ejercicio = st.selectbox("Ejercicio fiscal", [str(y) for y in range(2020, 2026)], index=5)
    trimestre = st.selectbox("Trimestre", ["1", "2", "3", "4"])

# Paso 2: Subida de facturas CSV con datos ya estructurados
st.markdown("### Paso 2 – Subida de facturas en formato CSV")

facturas = []

uploaded_files = st.file_uploader("Sube aquí tus facturas en formato CSV", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
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

if facturas:
    st.markdown("#### Facturas cargadas:")
    df_facturas = pd.DataFrame(facturas)
    edited_df = st.data_editor(df_facturas, num_rows="dynamic")

    ingresos = edited_df["base"].sum()
    retenciones_total = edited_df["retencion"].sum()
    gastos = 0.0  # No gastos automáticos aquí

else:
    st.info("No se han subido facturas.")

# Paso 3: Gastos manuales
st.markdown("### Paso 3 – Gastos deducibles adicionales")
gastos_manual = st.number_input("Introduce gastos deducibles adicionales", min_value=0.0, step=50.0, format="%.2f")

# Paso 4: Retenciones y pagos fraccionados
st.markdown("### Paso 4 – Retenciones y pagos fraccionados")
retenciones_input = st.number_input("IRPF retenido por clientes", min_value=0.0, step=50.0, format="%.2f", value=retenciones_total if facturas else 0.0)
pagos_previos = st.number_input("Pagos fraccionados realizados en el año", min_value=0.0, step=50.0, format="%.2f")

# Paso 5: Cálculo y resultados
if st.button("Calcular declaración"):
    rendimiento_neto = ingresos - (gastos + gastos_manual)
    porcentaje_fraccionado = 0.20  # Simplificado para ambos regímenes
    pago_fraccionado = max(0, rendimiento_neto * porcentaje_fraccionado)

    resultado_final = pago_fraccionado - retenciones_input - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado de la declaración")

    st.write(f"**Ingresos totales:** {ingresos:.2f} €")
    st.write(f"**Gastos totales:** {(gastos + gastos_manual):.2f} €")
    st.write(f"**Rendimiento neto (Ingresos - Gastos):** {rendimiento_neto:.2f} €")
    st.write(f"**Pago fraccionado (20% sobre rendimiento):** {pago_fraccionado:.2f} €")
    st.write(f"**IRPF retenido por clientes:** {retenciones_input:.2f} €")
    st.write(f"**Pagos fraccionados realizados:** {pagos_previos:.2f} €")

    if resultado_final >= 0:
        st.success(f"**Importe a ingresar:** {resultado_final:.2f} €")
    else:
        st.info(f"**Importe a compensar (a favor):** {abs(resultado_final):.2f} €")

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

    csv = df_resumen.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="resumen_modelo_130.csv">📥 Descargar resumen CSV</a>'
    st.markdown(href, unsafe_allow_html=True)

