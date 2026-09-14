import streamlit as st
import numpy as np
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Oil & Gas Engineering Analytics Suite",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS: paleta industrial elegante, fondo oscuro acero y tarjetas con contraste técnico
st.markdown("""
    <style>
        .stApp {
            background-color: #0b1118;
            color: #e2e8f0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .og-card {
            background-color: #151f2c;
            border: 1px solid #233549;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
        }
        .og-card.normal { border-left: 5px solid #10b981; }
        .og-card.observacion { border-left: 5px solid #f59e0b; }
        .og-card.critico { border-left: 5px solid #ef4444; }

        .metric-label {
            font-size: 0.8rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 600;
            color: #f8fafc;
        }
        .metric-sub {
            font-size: 0.75rem;
            color: #64748b;
            margin-top: 0.2rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #0f1722;
            padding: 6px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
            font-weight: 500;
            border-radius: 6px;
            padding: 8px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e2d42 !important;
            color: #38bdf8 !important;
        }
    </style>
""", unsafe_allow_html=True)


def tarjeta_metrica(titulo: str, valor: str, subtitulo: str = "", estado: str = ""):
    clase_estado = f" {estado}" if estado else ""
    html = f"""
    <div class="og-card{clase_estado}">
        <div class="metric-label">{titulo}</div>
        <div class="metric-value">{valor}</div>
        {"<div class='metric-sub'>" + subtitulo + "</div>" if subtitulo else ""}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def componente_js_auditoria():
    codigo_html = """
    <div id="js-box" style="background:#111b27; border:1px solid #1f2f45; border-radius:6px; padding:10px 14px; color:#94a3b8; font-family:monospace; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span>⚡ SISTEMA OPERATIVO: </span>
            <span id="system-status" style="color:#38bdf8; font-weight:bold;">EN LÍNEA</span>
        </div>
        <div>
            <button id="btn-clock" style="background:#1e2d42; border:1px solid #334e68; color:#f8fafc; padding:4px 10px; border-radius:4px; cursor:pointer;">
                Validar Sesión
            </button>
            <span id="session-time" style="margin-left:8px; color:#64748b;">--:--:--</span>
        </div>
    </div>

    <script>
        function updateClock() {
            const now = new Date();
            document.getElementById("session-time").innerText = now.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();

        document.getElementById("btn-clock").addEventListener("click", function() {
            const st = document.getElementById("system-status");
            st.innerText = "SESIÓN ACTIVA #" + Math.floor(Math.random() * 90000 + 10000);
            st.style.color = "#10b981";
        });
    </script>
    """
    components.html(codigo_html, height=52)


# ==========================================
# 2. FUNCIONES DE CÁLCULO
# ==========================================
def calcular_ipr_compuesta(pr: float, pb: float, j: float, pwf: float):
    qb = j * (pr - pb)
    qmax = qb + (j * pb / 1.8)
    
    if pwf >= pb:
        qo_actual = j * (pr - pwf)
        regimen = "Subsaturado (Flujo Lineal - Darcy)"
    else:
        qo_actual = qb + (j * pb / 1.8) * (1.0 - 0.2 * (pwf / pb) - 0.8 * ((pwf / pb) ** 2))
        regimen = "Saturado bifásico (Modelo Vogel)"
        
    pwf_pts = np.linspace(0, pr, 100)
    qo_pts = []
    for p in pwf_pts:
        if p >= pb:
            q = j * (pr - p)
        else:
            q = qb + (j * pb / 1.8) * (1.0 - 0.2 * (p / pb) - 0.8 * ((p / pb) ** 2))
        qo_pts.append(max(q, 0.0))
        
    return qo_actual, qb, qmax, regimen, pwf_pts, np.array(qo_pts)


def calcular_hidrostatica(mw: float, tvd: float, pform: float):
    gh = 0.052 * mw
    ph = gh * tvd
    delta_p = ph - pform
    
    if abs(delta_p) <= 50.0:
        condicion = "Balance Aproximado"
        color_tipo = "observacion"
    elif delta_p > 50.0:
        condicion = "Sobrebalance (Ph > Pf)"
        color_tipo = "normal"
    else:
        condicion = "Bajo Balance (Kick Risk - Ph < Pf)"
        color_tipo = "critico"
        
    return gh, ph, delta_p, condicion, color_tipo


def calcular_poes(area: float, h: float, ntg: float, phi: float, swi: float, boi: float, fr: float):
    hn = h * ntg
    poes_stb = (7758.0 * area * hn * phi * (1.0 - swi)) / boi
    poes_mmstb = poes_stb / 1e6
    recuperable_stb = poes_stb * fr
    recuperable_mmstb = recuperable_stb / 1e6
    return hn, poes_stb, poes_mmstb, recuperable_stb, recuperable_mmstb


# ==========================================
# 3. NAVEGACIÓN PRINCIPAL
# ==========================================
with st.sidebar:
    st.markdown("### **SPE Ecuador Section**")
    st.caption("Bootcamp: Data Analytics for Oil & Gas")
    st.divider()
    opcion_navegacion = st.radio(
        "Módulos",
        ["Home", "Ejercicios"],
        index=0,
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Módulo 1: Streamlit, HTML, CSS y JS")


# ==========================================
# 4. PÁGINA: HOME
# ==========================================
if opcion_navegacion == "Home":
    st.title("🛢️ Oil & Gas Analytics Suite")
    st.caption("Plataforma técnica computacional para análisis de Producción, Perforación y Reservorios")
    
    componente_js_auditoria()
    st.write("")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="og-card">
            <h3 style="color:#38bdf8; margin-top:0;">Propósito de la Aplicación</h3>
            <p style="color:#cbd5e1; line-height:1.6; font-size: 0.95rem;">
                Esta plataforma web consolida herramientas analíticas para la resolución de cálculos fundamentales en 
                ingeniería de petróleo. A través de una interfaz moderna y reactiva, permite evaluar el comportamiento 
                de afluencia en pozos (IPR Compuesta), verificar el equilibrio de presiones en perforación (gradiente y Ph)
                y computar volumétricamente el volumen de hidrocarburo original en sitio (POES) junto con sus reservas recuperables.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            tarjeta_metrica("Módulo 1", "Producción", "IPR Darcy + Vogel (Subsaturado)")
        with c2:
            tarjeta_metrica("Módulo 2", "Perforación", "Columna Hidrostática & Balance")
        with c3:
            tarjeta_metrica("Módulo 3", "Reservorios", "POES Volumétrico & Recobro")

    with col2:
        st.markdown("""
        <div class="og-card">
            <div class="metric-label">Desarrollador / Participante</div>
            <div style="font-size:1.1rem; font-weight:600; color:#f8fafc; margin-top:4px;">
                Ing. Daniel Nicolás Peralvo Vela
            </div>
            <div style="color:#38bdf8; font-size:0.85rem; margin-top:2px;">Petroleum Engineer</div>
            <hr style="border:0; border-top:1px solid #233549; margin:12px 0;">
            <div class="metric-label">Programa Técnico</div>
            <div style="color:#cbd5e1; font-size:0.85rem;">Bootcamp Data Analytics for Oil & Gas</div>
            <div class="metric-label" style="margin-top:8px;">Organización</div>
            <div style="color:#cbd5e1; font-size:0.85rem;">SPE International - Sección Ecuador</div>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# 5. PÁGINA: EJERCICIOS (TABS OBLIGATORIOS)
# ==========================================
else:
    st.title("⚙️ Módulos Técnicos Especializados")
    tab_prod, tab_perf, tab_res = st.tabs([
        "🛢️ Producción (IPR Vogel)",
        "🚧 Perforación (Hidrostática)",
        "🌐 Reservorios (POES)"
    ])

    # --- TAB PRODUCCIÓN ---
    with tab_prod:
        st.subheader("Rendimiento de Afluencia - IPR Compuesta (Darcy / Vogel)")
        st.caption("Cálculo para yacimientos subsaturados considerando la presión de burbuja (Pb)")
        
        c_in, c_out = st.columns([1, 2])
        with c_in:
            st.markdown("**Parámetros de Entrada**")
            pr = st.number_input("Presión de Reservorio, Pr [psi]", value=3200.0, step=50.0)
            pb = st.number_input("Presión de Burbuja, Pb [psi]", value=2100.0, step=50.0)
            j = st.number_input("Índice de Productividad, J [STB/d/psi]", value=1.85, step=0.1)
            pwf = st.number_input("Presión Fondo Fluyente, Pwf [psi]", value=1650.0, step=50.0)
            
            errores = []
            if pr <= 0 or pb <= 0 or j <= 0 or pwf < 0:
                errores.append("Los parámetros deben ser positivos.")
            if pr <= pb:
                errores.append("Pr debe ser mayor que Pb para reservorio subsaturado.")
            if pwf > pr:
                errores.append("Pwf no puede ser mayor que Pr.")

        with c_out:
            if errores:
                for err in errores:
                    st.error(f"⚠️ {err}")
            else:
                qo, qb, qmax, regimen, pwf_pts, qo_pts = calcular_ipr_compuesta(pr, pb, j, pwf)
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    tarjeta_metrica("Caudal Operativo (qo)", f"{qo:,.1f} STB/d", f"A Pwf = {pwf:.0f} psi")
                with m2:
                    tarjeta_metrica("Caudal en Pb (qb)", f"{qb:,.1f} STB/d", "Límite lineal Darcy")
                with m3:
                    tarjeta_metrica("Caudal Máximo (AOF)", f"{qmax:,.1f} STB/d", "A Pwf = 0 psi")
                    
                st.info(f"**Régimen de Operación:** {regimen}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=qo_pts, y=pwf_pts, mode='lines', name='Curva IPR', line=dict(color='#38bdf8', width=2.5)))
                fig.add_trace(go.Scatter(x=[qo], y=[pwf], mode='markers', name='Punto Evaluado', marker=dict(color='#f59e0b', size=11, symbol='diamond')))
                fig.add_hline(y=pb, line_dash="dash", line_color="#ef4444", annotation_text=f"Pb = {pb:.0f} psi")
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#111a24",
                    title="Curva IPR (Pwf vs. qo)", xaxis_title="Caudal de Líquido, qo [STB/d]", yaxis_title="Pwf [psi]",
                    margin=dict(l=20, r=20, t=40, b=20), height=380, legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)

    # --- TAB PERFORACIÓN ---
    with tab_perf:
        st.subheader("Presión Hidrostática y Margen de Balance")
        st.caption("Cálculo hidrostático basado en la Profundidad Vertical Verdadera (TVD)")
        
        c_in2, c_out2 = st.columns([1, 2])
        with c_in2:
            st.markdown("**Parámetros de Perforación**")
            mw = st.number_input("Densidad del Lodo, MW [ppg]", value=10.4, step=0.1)
            md = st.number_input("Profundidad Medida, MD [ft]", value=9800.0, step=100.0)
            tvd = st.number_input("Profundidad Vertical, TVD [ft]", value=9200.0, step=100.0)
            pform = st.number_input("Presión de Formación, Pf [psi]", value=4650.0, step=50.0)
            
            errores2 = []
            if mw <= 0 or md <= 0 or tvd <= 0 or pform < 0:
                errores2.append("Parámetros deben ser mayores a cero.")
            if tvd > md:
                errores2.append("Inconsistencia: TVD no puede ser mayor que MD.")

        with c_out2:
            if errores2:
                for err in errores2:
                    st.error(f"⚠️ {err}")
            else:
                gh, ph, delta_p, condicion, color_tipo = calcular_hidrostatica(mw, tvd, pform)
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    tarjeta_metrica("Gradiente Hidrostático", f"{gh:.4f} psi/ft", f"MW: {mw:.1f} ppg")
                with m2:
                    tarjeta_metrica("Presión Hidrostática (Ph)", f"{ph:,.1f} psi", f"A {tvd:,.0f} ft TVD")
                with m3:
                    tarjeta_metrica("Diferencial (ΔP)", f"{delta_p:+,.1f} psi", condicion, estado=color_tipo)

                fig_perf = go.Figure()
                fig_perf.add_trace(go.Scatter(x=[0, ph], y=[0, tvd], mode='lines+markers', name='Presión Hidrostática', line=dict(color='#10b981', width=2.5)))
                fig_perf.add_trace(go.Scatter(x=[pform], y=[tvd], mode='markers', name='Presión Formación', marker=dict(color='#ef4444', size=11, symbol='circle')))
                fig_perf.update_layout(
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#111a24",
                    title="Perfil de Presión vs. TVD", xaxis_title="Presión [psi]", yaxis_title="TVD [ft]",
                    yaxis=dict(autorange="reversed"), margin=dict(l=20, r=20, t=40, b=20), height=380, legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_perf, use_container_width=True)

    # --- TAB RESERVORIOS ---
    with tab_res:
        st.subheader("Estimación Volumétrica del POES y Reservas Recuperables")
        st.caption("Cálculo de Petróleo Original en Sitio mediante propiedades de yacimiento y PVT")
        
        c_in3, c_out3 = st.columns([1, 2])
        with c_in3:
            st.markdown("**Propiedades Petrofísicas**")
            area = st.number_input("Área, A [acres]", value=850.0, step=50.0)
            h = st.number_input("Espesor Bruto, h [ft]", value=95.0, step=5.0)
            ntg = st.slider("Net-to-Gross (NTG)", min_value=0.1, max_value=1.0, value=0.78, step=0.01)
            phi = st.slider("Porosidad Efectiva (φ)", min_value=0.05, max_value=0.35, value=0.19, step=0.01)
            swi = st.slider("Saturación Inicial de Agua (Swi)", min_value=0.05, max_value=0.80, value=0.28, step=0.01)
            boi = st.number_input("Factor Volumétrico Inicial, Boi [rb/STB]", value=1.24, step=0.02)
            fr = st.slider("Factor de Recobro (FR)", min_value=0.05, max_value=0.60, value=0.25, step=0.01)
            
            errores3 = []
            if area <= 0 or h <= 0 or boi <= 0:
                errores3.append("Área, espesor y Boi deben ser mayores a 0.")

        with c_out3:
            if errores3:
                for err in errores3:
                    st.error(f"⚠️ {err}")
            else:
                hn, poes_stb, poes_mmstb, rec_stb, rec_mmstb = calcular_poes(area, h, ntg, phi, swi, boi, fr)
                
                m1, m2, m3 = st.columns(3)
                with m1:
                    tarjeta_metrica("Espesor Neto (hn)", f"{hn:.1f} ft", f"Gross h: {h:.0f} ft (NTG: {ntg*100:.0f}%)")
                with m2:
                    tarjeta_metrica("POES Total", f"{poes_mmstb:,.2f} MMSTB", f"{poes_stb:,.0f} STB")
                with m3:
                    tarjeta_metrica("Petróleo Recuperable", f"{rec_mmstb:,.2f} MMSTB", f"FR: {fr*100:.1f}%")

                remanente = poes_mmstb - rec_mmstb
                fig_bar = go.Figure(data=[
                    go.Bar(name='Recuperable', x=['Volumen'], y=[rec_mmstb], marker_color='#10b981'),
                    go.Bar(name='No Recuperable', x=['Volumen'], y=[remanente], marker_color='#334e68')
                ])
                fig_bar.update_layout(
                    barmode='stack', template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#111a24",
                    title=f"Distribución del POES: {poes_mmstb:,.2f} MMSTB", yaxis_title="MMSTB",
                    margin=dict(l=20, r=20, t=40, b=20), height=350, legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig_bar, use_container_width=True)