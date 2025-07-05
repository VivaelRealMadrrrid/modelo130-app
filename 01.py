import streamlit as st

st.set_page_config(page_title="Declaración Modelo 130", layout="centered")

st.title("🧾 Declaración automática Modelo 130")
st.subheader("Paso 1 – Tus datos del trimestre")

# Entrada de datos del usuario
ingresos = st.number_input("Ingresos acumulados (sin IVA)", min_value=0.0, step=100.0, format="%.2f")
gastos = st.number_input("Gastos deducibles acumulados", min_value=0.0, step=100.0, format="%.2f")
retenciones = st.number_input("IRPF retenido por clientes", min_value=0.0, step=50.0, format="%.2f")
pagos_previos = st.number_input("Pagos ya realizados este año", min_value=0.0, step=50.0, format="%.2f")

# Cálculo y resultado
if st.button("Calcular resultado"):
    rendimiento = ingresos - gastos
    fraccionado = max(0, rendimiento * 0.20)
    resultado = fraccionado - retenciones - pagos_previos

    st.markdown("---")
    st.subheader("📊 Resultado del trimestre")
    st.write(f"**Rendimiento neto:** {rendimiento:.2f} €")
    st.write(f"**20 % del rendimiento (pago fraccionado):** {fraccionado:.2f} €")
    st.write(f"**Resultado final a pagar o compensar:** `{resultado:.2f} €`")
