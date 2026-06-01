# ----- Librerías ---- #
import streamlit as st
from PIL import Image
import time

# IMPORTANTE:
# `st.set_page_config(...)` debe ejecutarse antes de cualquier otro comando de Streamlit.
img = Image.open('logoicon.png')
st.set_page_config(page_title="Formularios TPZ", page_icon=img, layout="wide")

import Autenticacion
import Procesos
import Notificaciones

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: Visible;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----- Inicialización de estados ---- #
if "Ingreso" not in st.session_state:
    st.session_state.Ingreso = False

if "paso_actual" not in st.session_state:
    st.session_state.paso_actual = "login"  # login, notificaciones, procesos

if "usuario_activo_cache" not in st.session_state:
    st.session_state.usuario_activo_cache = None

if "usuario_login_cache" not in st.session_state:
    st.session_state.usuario_login_cache = None


def _inicializar_banderas():
    flags = [
        "Procesos", "Historial", "Capacitacion", "Otros_Registros", "Bonos_Extras", "Correcciones", "Salir",
        "FMI", "CC_FMI", "Postcampo_FMI", "Postcampo_CC_FMI", "Consulta_Campo", "Restitucion_Tierras",
        "Revision_Segregados", "Calidad_externa_XTF", "Precampo", "Precampo_Juridico", "Descarga_Partidas_Juridico",
        "Asignacion_Partidas", "CC_Precampo", "Vinculacion_Precampo", "Preparacion_Insumos", "Entregas_Postcampo",
        "Revision_Campo", "Postcampo", "CC_Postcampo", "CC_Precampo_Juridico", "CC_Vinculacion_precampo",
        "Estado_UIT_Hito"
    ]
    for key in flags:
        st.session_state[key] = False


def _redirigir_procesos(usuario_login, puesto_login, perfil_login):
    """
    Redirige a la pantalla de procesos según el perfil del usuario
    """
    # Mostrar información del usuario en sidebar
    with st.sidebar:
        st.markdown("---")
        st.write(f"👤 **Usuario:** {usuario_login}")
        st.write(f"💼 **Puesto:** {puesto_login}")
        st.markdown("---")
    
    # Redirigir según perfil
    if perfil_login == "1":
        Procesos.Procesos1(usuario_login, puesto_login)
    elif perfil_login == "2":
        Procesos.Procesos2(usuario_login, puesto_login)
    elif perfil_login == "3":
        Procesos.Procesos3(usuario_login, puesto_login)
    else:
        st.error(f"❌ Perfil no reconocido: {perfil_login}")
        st.info("Contacta al administrador del sistema")


# ==================== PANTALLA DE LOGIN ==================== #
if st.session_state.paso_actual == "login":
    
    pivot = 0
    
    placeholder1_1 = st.sidebar.empty()
    titulo_1 = placeholder1_1.title("Ingreso")
    
    placeholder2_1 = st.sidebar.empty()
    usuario = placeholder2_1.text_input("Usuario", key="usuario_login")
    
    placeholder3_1 = st.sidebar.empty()
    contraseña_1 = placeholder3_1.text_input("Contraseña", type='password', key="contraseña_1")
    
    placeholder4_1 = st.sidebar.empty()
    iniciar_sesion_1 = placeholder4_1.button("Iniciar sesión", key="iniciar_sesion_1")
    
    # Si ya había ingresado antes (por si acaso)
    if st.session_state.Ingreso:
        st.session_state.Ingreso = True
        placeholder1_1.empty()
        placeholder2_1.empty()
        placeholder3_1.empty()
        placeholder4_1.empty()
        
        usuario_activo = Autenticacion.obtener_usuario_activo(usuario)
        if usuario_activo:
            _redirigir_procesos(usuario, usuario_activo['puesto'], str(usuario_activo['perfil']))
            pivot = pivot + 1
    
    # Validación del login
    if iniciar_sesion_1:
        if usuario == '' or contraseña_1 == '':
            st.error('Favor ingresar sus credenciales')
        else:
            usuario_activo = Autenticacion.obtener_usuario_activo(usuario)
            
            if not usuario_activo:
                st.error('El usuario no existe, intente de nuevo')
            else:
                if usuario_activo['contraseña'] == contraseña_1:
                    st.success(f"¡Saludos {usuario_activo['nombre']}!")
                    
                    # Limpiar sidebar
                    placeholder1_1.empty()
                    placeholder2_1.empty()
                    placeholder3_1.empty()
                    placeholder4_1.empty()
                    
                    # Guardar en sesión para el siguiente paso
                    st.session_state.usuario_activo_cache = usuario_activo
                    st.session_state.usuario_login_cache = usuario
                    
                    # Cambiar al paso de notificaciones
                    st.session_state.paso_actual = "notificaciones"
                    st.rerun()
                    
                else:
                    st.error('Contraseña incorrecta, intente de nuevo')
    
    # Mensajes generales (solo si no hay login exitoso)
    if pivot != 1 and st.session_state.paso_actual == "login":
        try:
            st.image(Image.open("logo.png"))
        except:
            st.image("logo.png")
        
        st.title("Telespazio Argentina S.A.")
        st.header("Aplicación de uso exclusivo para el personal de Telespazio Argentina S.A.")
        st.subheader("Proyecto Perú")
        st.subheader("Para soporte técnico favor escribir a brayan.rojas@tpzcr.com")


# ==================== PANTALLA DE NOTIFICACIONES ==================== #
elif st.session_state.paso_actual == "notificaciones":
    
    usuario_activo = st.session_state.usuario_activo_cache
    usuario = st.session_state.usuario_login_cache
    
    if usuario_activo:
        
        # Mostrar notificaciones de rechazos pendientes
        # Esta función retorna True si debe redirigir automáticamente
        redirigir_automatico = Notificaciones.mostrar_notificaciones_rechazos(
            usuario, 
            usuario_activo['nombre']
        )
        
        # Si no hay rechazos, redirigir automáticamente a procesos
        if redirigir_automatico:
            _inicializar_banderas()
            st.session_state.paso_actual = "procesos"
            time.sleep(0.5)  # Pequeña pausa para que se vea el mensaje
            st.rerun()
        
        # Si hay rechazos, mostrar solo el botón para continuar
        else:
            st.markdown("---")
            
            # Botón para continuar a procesos centrado
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("📊 Continuar a Procesos", type="primary", use_container_width=True):
                    _inicializar_banderas()
                    st.session_state.paso_actual = "procesos"
                    st.rerun()
    
    else:
        # Si no hay usuario activo, volver al login
        st.session_state.paso_actual = "login"
        st.rerun()


# ==================== PANTALLA DE PROCESOS ==================== #
elif st.session_state.paso_actual == "procesos":
    
    usuario_activo = st.session_state.usuario_activo_cache
    usuario = st.session_state.usuario_login_cache
    
    if usuario_activo:
        _redirigir_procesos(usuario, usuario_activo['puesto'], str(usuario_activo['perfil']))
    else:
        # Si no hay usuario activo, volver al login
        st.session_state.paso_actual = "login"
        st.rerun()


# ==================== PIE DE PÁGINA (solo visible en login) ==================== #
if st.session_state.paso_actual == "login":
    footer = """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 2px;
            font-size: 12px;
            color: #555;
         }
         .footer a {
            color: tomato;
            text-decoration: none;
            font-weight: bold;
         }
        </style>
        <div class="footer">
            <p>V.1.6 © 2025 Telespazio Argentina S.A. | <a href="https://www.telespazio.com/en" target="_blank">Visit our website</a></p>
        </div>
    """
    st.markdown(footer, unsafe_allow_html=True)
