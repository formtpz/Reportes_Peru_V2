# Salir.py
import streamlit as st


def Salir():
    """
    Cierra la sesión actual y vuelve a la pantalla de login
    """
    # Limpiar todos los estados de sesión relacionados con el usuario
    st.session_state.paso_actual = "login"
    st.session_state.usuario_activo_cache = None
    st.session_state.usuario_login_cache = None
    st.session_state.Ingreso = False
    st.session_state.Procesos = False
    st.session_state.Salir = False
    
    # Limpiar banderas de procesos
    flags = [
        "Historial", "Capacitacion", "Otros_Registros", "Bonos_Extras", "Correcciones",
        "Precampo_Juridico", "Descarga_Partidas_Juridico", "CC_Precampo_Juridico",
        "Asignacion_Partidas", "Precampo", "CC_Precampo", "Vinculacion_Precampo",
        "Preparacion_Insumos", "Entregas_Postcampo", "Postcampo", "CC_Postcampo",
        "CC_Vinculacion_Precampo", "Restitucion_Tierras", "Revision_Segregados",
        "Estado_UIT_Hito", "Consulta_Campo", "FMI", "CC_FMI", "Postcampo_FMI",
        "Postcampo_CC_FMI", "Revision_Campo", "Calidad_externa_XTF"
    ]
    for flag in flags:
        if flag in st.session_state:
            st.session_state[flag] = False
    
    # Recargar la página para mostrar el login
    st.rerun()
