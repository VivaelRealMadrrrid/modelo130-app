import streamlit as st
import pandas as pd
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

# -- Entrada manual de datos económicos --
st.markdown("### Paso 2 – Ingresos y gastos acumulados")
st.markdown("**(Puede introducir manualmente los totales o subir archivos CSV para importarlos automáticamente)**")

# Subida y procesado de CSV para ingresos
ingresos_totales = 0.0
if st.checkbox("Subir archivo CSV con facturas emitidas (ingresos)"):
    uploaded_file = st.file_uploader("Seleccione archivo CSV ingresos", type=["csv"])
    if uploaded_file is not None:
        try:
            df_ingresos = pd.read_csv(uploaded_file)
            if "importe_sin_iva" in df_ingresos.columns:
                ingresos_totales = df_ingresos["importe_sin_iva"].sum()
                st.success(f"Ingresos totales calculados: {ingresos_totales:.2f} €")
            else:
                st.error("El archivo CSV debe contener una columna llamada 'importe_sin_iva'")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# Entrada manual si no sube archivo
if ingresos_totales == 0:
    ingresos_totales = st.number_input("Ingresos acumulados (sin IVA)", min_value=0.0, step=100.0, format="%.2f")

# Subida y procesado de CSV para gastos
gastos_totales = 0.0
if st.checkbox("Subir archivo CSV con facturas recibidas (gastos deducibles)"):
    uploaded_gastos = st.file_uploader("Seleccione archivo CSV gastos", type=["csv"])
    if uploaded_gastos is not None:
        try:
            df_gastos = pd.read_csv(uploaded_gastos)
            if "importe" in df_gastos.columns:
                gastos_totales = df_gastos["importe"].sum()
                st.success(f"Gastos totales calculados: {gastos_totales:.2f} €")
            else:
                st.error("El archivo CSV debe contener una columna llamada 'importe'")
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

if gastos_totales == 0:
    gastos_totales = st.number_input("Gastos deducibles acumulados", min_value=0.0, step=100.0, format="%.2f")

# Retenciones y pagos previos
retenciones = st.number_input("IRPF retenido por clientes", min_value=0.0, step=50.0, format="%.2f")
pagos_previos = st.number_input("Pagos fraccionados realizados este año", min_value=0.0, step=50.0, format="%.2f")

# Validaciones básicas
if ingresos_totales < gastos_totales:
    st.warning("Los gastos deducibles superan a los ingresos, revise los datos.")

# Cálculo y resultado
if st.button("Calcular declaración"):
    rendimiento = ingresos_totales - gastos_totales
    fraccionado = max(0, rendimiento * 0.20)
    resultado = fraccionado - retenciones - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado del trimestre")
    st.write(f"**Rendimiento neto (Ingresos - Gastos):** {rendimiento:.2f} €")
    st.write(f"**20 % del rendimiento (Pago fraccionado):** {fraccionado:.2f} €")
    st.write(f"**Retenciones soportadas:** {retenciones:.2f} €")
    st.write(f"**Pagos fraccionados previos:** {pagos_previos:.2f} €")
    if resultado >= 0:
        st.success(f"**Importe a ingresar:** {resultado:.2f} €")
    else:
        st.info(f"**Importe a compensar:** {abs(resultado):.2f} €")

    st.markdown("""
    ---
    **Notas:**  
    - El rendimiento neto se calcula como la diferencia entre ingresos y gastos deducibles.  
    - El pago fraccionado es el 20 % de ese rendimiento.  
    - Del pago fraccionado se descuentan las retenciones y pagos realizados anteriormente.  
    - En caso de que el resultado sea negativo, el importe puede compensarse en siguientes periodos.  
    """)


