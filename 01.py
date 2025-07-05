import streamlit as st
import pandas as pd

st.set_page_config(page_title="Declaración Modelo 130", layout="centered")

st.title("🧾 Declaración automática Modelo 130")
st.subheader("Paso 1 – Datos fiscales del declarante")

with st.expander("Datos personales y fiscales"):
    nif = st.text_input("NIF/NIE")
    nombre = st.text_input("Nombre completo o razón social")
    regimen = st.selectbox("Régimen fiscal", ["Estimación directa simplificada", "Estimación directa normal"])
    iae = st.text_input("Código de actividad económica (IAE)")
    ejercicio = st.selectbox("Ejercicio fiscal", [str(y) for y in range(2020, 2026)], index=5)
    trimestre = st.selectbox("Trimestre", ["1", "2", "3", "4"])

st.markdown("### Paso 2 – Ingresos y gastos")
st.markdown("Puedes introducir manualmente los datos o subir archivos `.csv` estructurados")

# INGRESOS
ingresos_totales = 0.0
st.markdown("#### Ingresos del trimestre")
if st.checkbox("Subir archivo CSV con facturas emitidas (ingresos)"):
    ingresos_csv = st.file_uploader("Selecciona archivo CSV de ingresos", type=["csv"])
    if ingresos_csv is not None:
        try:
            df_ingresos = pd.read_csv(ingresos_csv)
            if "importe_sin_iva" in df_ingresos.columns:
                ingresos_totales = df_ingresos["importe_sin_iva"].sum()
                st.success(f"Ingresos totales calculados: {ingresos_totales:.2f} €")
            else:
                st.error("El archivo debe contener una columna llamada 'importe_sin_iva'")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
if ingresos_totales == 0:
    ingresos_totales = st.number_input("Ingresos acumulados (sin IVA)", min_value=0.0, step=100.0, format="%.2f")

# GASTOS
gastos_totales = 0.0
st.markdown("#### Gastos deducibles del trimestre")
if st.checkbox("Subir archivo CSV con facturas recibidas (gastos)"):
    gastos_csv = st.file_uploader("Selecciona archivo CSV de gastos", type=["csv"])
    if gastos_csv is not None:
        try:
            df_gastos = pd.read_csv(gastos_csv)
            if "importe" in df_gastos.columns:
                gastos_totales = df_gastos["importe"].sum()
                st.success(f"Gastos deducibles calculados: {gastos_totales:.2f} €")
            else:
                st.error("El archivo debe contener una columna llamada 'importe'")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
if gastos_totales == 0:
    gastos_totales = st.number_input("Gastos deducibles acumulados", min_value=0.0, step=100.0, format="%.2f")

# RETENCIONES Y PAGOS
retenciones = st.number_input("IRPF retenido por clientes", min_value=0.0, step=50.0, format="%.2f")
pagos_previos = st.number_input("Pagos fraccionados ya realizados en el año", min_value=0.0, step=50.0, format="%.2f")

# CÁLCULO FINAL
if st.button("Calcular declaración"):
    rendimiento = ingresos_totales - gastos_totales
    fraccionado = max(0, rendimiento * 0.20)
    resultado = fraccionado - retenciones - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado del trimestre")
    st.write(f"**Rendimiento neto (ingresos - gastos):** {rendimiento:.2f} €")
    st.write(f"**20 % del rendimiento (pago fraccionado):** {fraccionado:.2f} €")
    st.write(f"**Retenciones soportadas:** {retenciones:.2f} €")
    st.write(f"**Pagos fraccionados anteriores:** {pagos_previos:.2f} €")
    
    if resultado >= 0:
        st.success(f"**Importe a ingresar:** {resultado:.2f} €")
    else:
        st.info(f"**Importe a compensar:** {abs(resultado):.2f} €")

    st.markdown("""
    ---
    **Notas:**  
    - Este resultado es orientativo.  
    - El cálculo parte de ingresos y gastos acumulados hasta el trimestre actual.  
    - Los pagos previos y retenciones reducen el importe a ingresar.  
    - El resultado negativo puede compensarse en trimestres siguientes.
    """)


