# ----- Librerías ---- #
import streamlit as st
import time

# Importaciones de módulos (se mantienen igual)
import Historial, Capacitacion, Otros_Registros, Correcciones, Bonos_Extras, Salir
import Precampo_Juridico, Descarga_Partidas_Juridico, Asignacion_Partidas, CC_Precampo_Juridico
import Consulta_Campo, Restitucion_Tierras, Revision_Segregados, Estado_UIT_Hito
import Precampo, CC_Precampo, Preparacion_Insumos, Entregas_Postcampo, Postcampo, CC_Postcampo
import CC_Vinculacion_Precampo, Vinculacion_Precampo

# ------------------- CONTADOR PARA REFRESCAR PÁGINA ------------------- #
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

if time.time() - st.session_state.start_time > 29 * 60:
    st.session_state.clear()
    st.rerun()

def auto_refresh(seconds=30600):
    st.markdown(
        f'<meta http-equiv="refresh" content="{seconds}">',
        unsafe_allow_html=True
    )

auto_refresh(30600)
# --------------------------------------------------------------------- #

def limpiar_sidebar_y_contenido(placeholder_list):
    """Vacía todos los placeholders proporcionados."""
    for ph in placeholder_list:
        if ph is not None:
            ph.empty()

def navegar_a(modulo_func, usuario, puesto, flag_name):
    """Establece flags de estado y llama al módulo correspondiente."""
    st.session_state.Procesos = True
    # Activar solo la bandera del módulo destino
    for key in ["Historial", "Capacitacion", "Otros_Registros", "Bonos_Extras",
                "Correcciones", "Precampo_Juridico", "Descarga_Partidas_Juridico",
                "CC_Precampo_Juridico", "Asignacion_Partidas", "Precampo", "CC_Precampo",
                "Vinculacion_Precampo", "Preparacion_Insumos", "Entregas_Postcampo",
                "Postcampo", "CC_Postcampo", "CC_Vinculacion_Precampo",
                "Restitucion_Tierras", "Revision_Segregados", "Estado_UIT_Hito"]:
        st.session_state[key] = (key == flag_name)
    modulo_func(usuario, puesto)

def menu_principal_por_perfil(usuario, puesto, perfil):
    """
    Muestra el menú de procesos según el perfil.
    Retorna True si se debe salir de la función (para evitar doble render).
    """
    # Inicializar estado si no existe
    if "Procesos" not in st.session_state:
        st.session_state.Procesos = False

    # Si ya estamos dentro de un submódulo, la función padre ya llamó al submódulo.
    if st.session_state.Procesos:
        return True

    # --- Crear placeholders (se guardan en lista para limpiar después) ---
    placeholders = []

    # Sidebar
    ph_sidebar = []
    ph_titulo = st.sidebar.empty()
    ph_titulo.title("Menú")
    ph_sidebar.append(ph_titulo)

    # Botones comunes del sidebar
    btn_historial = st.sidebar.empty()
    ph_sidebar.append(btn_historial)
    btn_capacitacion = st.sidebar.empty()
    ph_sidebar.append(btn_capacitacion)
    btn_otros = st.sidebar.empty()
    ph_sidebar.append(btn_otros)
    btn_bonos = st.sidebar.empty()
    ph_sidebar.append(btn_bonos)
    btn_correcciones = st.sidebar.empty()
    ph_sidebar.append(btn_correcciones)
    btn_salir = st.sidebar.empty()
    ph_sidebar.append(btn_salir)

    # Contenido principal
    ph_main = []
    titulo_procesos = st.empty()
    ph_main.append(titulo_procesos)

    # Lista de placeholders de botones de procesos
    botones_procesos = []

    # --- Mostrar botones según perfil ---
    titulo_procesos.title("Procesos")

    if perfil == "1":  # Perfil completo
        # Botones Jurídicos (Naranja)
        btn_precampo_jur = st.empty()
        btn_descarga_partidas = st.empty()
        btn_cc_precampo_jur = st.empty()
        btn_asig_partidas = st.empty()
        
        # Botones Precampo (Verde)
        btn_precampo = st.empty()
        btn_cc_precampo = st.empty()
        btn_vinculacion = st.empty()
        btn_cc_vinculacion = st.empty()
        
        # Botones Postcampo (Azul)
        btn_prep_insumos = st.empty()
        btn_entregas = st.empty()
        btn_postcampo = st.empty()
        btn_cc_postcampo = st.empty()
        btn_estado_uit = st.empty()
        
        # Agregar todos a la lista de limpieza
        botones_procesos = [btn_precampo_jur, btn_descarga_partidas, btn_cc_precampo_jur, btn_asig_partidas,
                           btn_precampo, btn_cc_precampo, btn_vinculacion, btn_cc_vinculacion,
                           btn_prep_insumos, btn_entregas, btn_postcampo, btn_cc_postcampo, btn_estado_uit]
    
        # --- BOTONES JURÍDICOS (Naranja) ---
        if btn_precampo_jur.button(":orange[Precampo Jurídico]", key="precampo_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Precampo_Juridico.Precampo_Juridico, usuario, puesto, "Precampo_Juridico")
            return True
        if btn_descarga_partidas.button(":orange[Descarga Partidas Jurídico]", key="descarga_partidas_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Descarga_Partidas_Juridico.Descarga_Partidas_Juridico, usuario, puesto, "Descarga_Partidas_Juridico")
            return True
        if btn_cc_precampo_jur.button(":orange[Control de Calidad Precampo Jurídico]", key="cc_precampo_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Precampo_Juridico.CC_Precampo_Juridico, usuario, puesto, "CC_Precampo_Juridico")
            return True
        if btn_asig_partidas.button(":orange[Asignación de Partidas]", key="asignacion_partidas"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Asignacion_Partidas.Asignacion_Partidas, usuario, puesto, "Asignacion_Partidas")
            return True
        
        # --- BOTONES PRECAMPO (Verde) ---
        if btn_precampo.button(":green[Precampo]", key="precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Precampo.Precampo, usuario, puesto, "Precampo")
            return True
        if btn_cc_precampo.button(":green[Control de Calidad Precampo]", key="cc_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Precampo.CC_Precampo, usuario, puesto, "CC_Precampo")
            return True
        if btn_vinculacion.button(":green[Vinculación Precampo]", key="vinculacion_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Vinculacion_Precampo.Vinculacion_Precampo, usuario, puesto, "Vinculacion_Precampo")
            return True
        if btn_cc_vinculacion.button(":green[Control de Calidad Vinculación Precampo]", key="cc_vinculacion_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Vinculacion_Precampo.CC_Vinculacion_Precampo, usuario, puesto, "CC_Vinculacion_Precampo")
            return True
        
        # --- BOTONES POSTCAMPO (Azul) ---
        # Botón deshabilitado (comentado)
        # if btn_prep_insumos.button(":gray[Preparación de Insumos]", key="preparacion_insumos_2", disabled=True):
        #     pass
        
        if btn_entregas.button(":blue[Entregas Postcampo]", key="entregas_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Entregas_Postcampo.Entregas_Postcampo, usuario, puesto, "Entregas_Postcampo")
            return True
        if btn_postcampo.button(":blue[Postcampo]", key="postcampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Postcampo.Postcampo, usuario, puesto, "Postcampo")
            return True
        if btn_cc_postcampo.button(":blue[Control de Calidad Postcampo]", key="cc_postcampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Postcampo.CC_Postcampo, usuario, puesto, "CC_Postcampo")
            return True
        
        # Botón deshabilitado (comentado)
        # if btn_estado_uit.button(":gray[Calidad Interna XTF]", key="estado_uit_hito_2", disabled=True):
        #     pass
    
    elif perfil == "2":  # Gabinete
        # Botones Precampo (Verde)
        btn_precampo = st.empty()
        btn_cc_precampo = st.empty()
        btn_vinculacion = st.empty()
        btn_cc_vinculacion = st.empty()
        
        # Botones Postcampo (Azul)
        btn_entregas = st.empty()
        btn_postcampo = st.empty()
        btn_cc_postcampo = st.empty()
        
        botones_procesos = [btn_precampo, btn_cc_precampo, btn_vinculacion, btn_cc_vinculacion,
                           btn_entregas, btn_postcampo, btn_cc_postcampo]
        
        # --- BOTONES PRECAMPO (Verde) ---
        if btn_precampo.button(":green[Precampo]", key="precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Precampo.Precampo, usuario, puesto, "Precampo")
            return True
        if btn_cc_precampo.button(":green[Control de Calidad Precampo]", key="cc_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Precampo.CC_Precampo, usuario, puesto, "CC_Precampo")
            return True
        if btn_vinculacion.button(":green[Vinculación Precampo]", key="vinculacion_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Vinculacion_Precampo.Vinculacion_Precampo, usuario, puesto, "Vinculacion_Precampo")
            return True
        if btn_cc_vinculacion.button(":green[Control de Calidad Vinculación Precampo]", key="cc_vinculacion_precampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Vinculacion_Precampo.CC_Vinculacion_Precampo, usuario, puesto, "CC_Vinculacion_Precampo")
            return True
        
        # --- BOTONES POSTCAMPO (Azul) ---
        if btn_entregas.button(":blue[Entregas Postcampo]", key="entregas_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Entregas_Postcampo.Entregas_Postcampo, usuario, puesto, "Entregas_Postcampo")
            return True
        if btn_postcampo.button(":blue[Postcampo]", key="postcampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Postcampo.Postcampo, usuario, puesto, "Postcampo")
            return True
        if btn_cc_postcampo.button(":blue[Control de Calidad Postcampo]", key="cc_postcampo_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Postcampo.CC_Postcampo, usuario, puesto, "CC_Postcampo")
            return True
    
    elif perfil == "3":  # Jurídicos
        # Botones Jurídicos (Naranja)
        btn_precampo_jur = st.empty()
        btn_descarga_partidas = st.empty()
        btn_cc_precampo_jur = st.empty()
        btn_asig_partidas = st.empty()
        
        botones_procesos = [btn_precampo_jur, btn_descarga_partidas, btn_cc_precampo_jur, btn_asig_partidas]
        
        # --- BOTONES JURÍDICOS (Naranja) ---
        if btn_precampo_jur.button(":orange[Precampo Jurídico]", key="precampo_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Precampo_Juridico.Precampo_Juridico, usuario, puesto, "Precampo_Juridico")
            return True
        if btn_descarga_partidas.button(":orange[Descarga Partidas Jurídico]", key="descarga_partidas_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Descarga_Partidas_Juridico.Descarga_Partidas_Juridico, usuario, puesto, "Descarga_Partidas_Juridico")
            return True
        if btn_cc_precampo_jur.button(":orange[Control de Calidad Precampo Jurídico]", key="cc_precampo_juridico_2"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(CC_Precampo_Juridico.CC_Precampo_Juridico, usuario, puesto, "CC_Precampo_Juridico")
            return True
        if btn_asig_partidas.button(":orange[Asignación de Partidas]", key="asignacion_partidas"):
            limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
            navegar_a(Asignacion_Partidas.Asignacion_Partidas, usuario, puesto, "Asignacion_Partidas")
            return True

    # --- Botones comunes del sidebar ---
    if btn_historial.button("Historial", key="historial_2"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        navegar_a(Historial.Historial, usuario, puesto, "Historial")
        return True
    if btn_capacitacion.button("Capacitaciones", key="capacitacion_2"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        navegar_a(Capacitacion.Capacitacion, usuario, puesto, "Capacitacion")
        return True
    if btn_otros.button("Otros Registros", key="otros_registros_2"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        navegar_a(Otros_Registros.Otros_Registros, usuario, puesto, "Otros_Registros")
        return True
    if btn_bonos.button("Bonos y Horas Extras", key="bonos_extras_2"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        navegar_a(Bonos_Extras.Bonos_Extras, usuario, puesto, "Bonos_Extras")
        return True
    if btn_correcciones.button("Solicitud Correcciones", key="correcciones"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        navegar_a(Correcciones.Correcciones, usuario, puesto, "Correcciones")
        return True
    if btn_salir.button("Salir", key="salir_2"):
        limpiar_sidebar_y_contenido(ph_sidebar + ph_main + botones_procesos)
        st.session_state.Ingreso = False
        st.session_state.Procesos = True
        st.session_state.Salir = True
        Salir.Salir()
        return True

    return False

# ------------------- FUNCIONES PÚBLICAS (mantienen compatibilidad) ------------------- #

def Procesos1(usuario, puesto):
    st.session_state.Ingreso = True
    # Si ya estamos en un submódulo, delegar
    if st.session_state.get("Procesos"):
        if st.session_state.get("Historial"):
            Historial.Historial(usuario, puesto)
        elif st.session_state.get("Capacitacion"):
            Capacitacion.Capacitacion(usuario, puesto)
        elif st.session_state.get("Otros_Registros"):
            Otros_Registros.Otros_Registros(usuario, puesto)
        elif st.session_state.get("Bonos_Extras"):
            Bonos_Extras.Bonos_Extras(usuario, puesto)
        elif st.session_state.get("Correcciones"):
            Correcciones.Correcciones(usuario, puesto)
        elif st.session_state.get("Precampo_Juridico"):
            Precampo_Juridico.Precampo_Juridico(usuario, puesto)
        elif st.session_state.get("Descarga_Partidas_Juridico"):
            Descarga_Partidas_Juridico.Descarga_Partidas_Juridico(usuario, puesto)
        elif st.session_state.get("CC_Precampo_Juridico"):
            CC_Precampo_Juridico.CC_Precampo_Juridico(usuario, puesto)
        elif st.session_state.get("Asignacion_Partidas"):
            Asignacion_Partidas.Asignacion_Partidas(usuario, puesto)
        elif st.session_state.get("Precampo"):
            Precampo.Precampo(usuario, puesto)
        elif st.session_state.get("CC_Precampo"):
            CC_Precampo.CC_Precampo(usuario, puesto)
        elif st.session_state.get("Vinculacion_Precampo"):
            Vinculacion_Precampo.Vinculacion_Precampo(usuario, puesto)
        elif st.session_state.get("Preparacion_Insumos"):
            Preparacion_Insumos.Preparacion_Insumos(usuario, puesto)
        elif st.session_state.get("Entregas_Postcampo"):
            Entregas_Postcampo.Entregas_Postcampo(usuario, puesto)
        elif st.session_state.get("Postcampo"):
            Postcampo.Postcampo(usuario, puesto)
        elif st.session_state.get("CC_Postcampo"):
            CC_Postcampo.CC_Postcampo(usuario, puesto)
        elif st.session_state.get("CC_Vinculacion_Precampo"):
            CC_Vinculacion_Precampo.CC_Vinculacion_Precampo(usuario, puesto)
        elif st.session_state.get("Estado_UIT_Hito"):
            Estado_UIT_Hito.Estado_UIT_Hito(usuario, puesto)
        # Si no hay bandera activa, se muestra el menú
        else:
            st.session_state.Procesos = False
            menu_principal_por_perfil(usuario, puesto, "1")
    else:
        menu_principal_por_perfil(usuario, puesto, "1")

def Procesos2(usuario, puesto):
    st.session_state.Ingreso = True
    if st.session_state.get("Procesos"):
        if st.session_state.get("Historial"):
            Historial.Historial(usuario, puesto)
        elif st.session_state.get("Capacitacion"):
            Capacitacion.Capacitacion(usuario, puesto)
        elif st.session_state.get("Otros_Registros"):
            Otros_Registros.Otros_Registros(usuario, puesto)
        elif st.session_state.get("Bonos_Extras"):
            Bonos_Extras.Bonos_Extras(usuario, puesto)
        elif st.session_state.get("Correcciones"):
            Correcciones.Correcciones(usuario, puesto)
        elif st.session_state.get("Precampo"):
            Precampo.Precampo(usuario, puesto)
        elif st.session_state.get("CC_Precampo"):
            CC_Precampo.CC_Precampo(usuario, puesto)
        elif st.session_state.get("Vinculacion_Precampo"):
            Vinculacion_Precampo.Vinculacion_Precampo(usuario, puesto)
        elif st.session_state.get("Entregas_Postcampo"):
            Entregas_Postcampo.Entregas_Postcampo(usuario, puesto)
        elif st.session_state.get("Postcampo"):
            Postcampo.Postcampo(usuario, puesto)
        elif st.session_state.get("CC_Postcampo"):
            CC_Postcampo.CC_Postcampo(usuario, puesto)
        elif st.session_state.get("CC_Vinculacion_Precampo"):
            CC_Vinculacion_Precampo.CC_Vinculacion_Precampo(usuario, puesto)
        else:
            st.session_state.Procesos = False
            menu_principal_por_perfil(usuario, puesto, "2")
    else:
        menu_principal_por_perfil(usuario, puesto, "2")

def Procesos3(usuario, puesto):
    st.session_state.Ingreso = True
    if st.session_state.get("Procesos"):
        if st.session_state.get("Historial"):
            Historial.Historial(usuario, puesto)
        elif st.session_state.get("Capacitacion"):
            Capacitacion.Capacitacion(usuario, puesto)
        elif st.session_state.get("Otros_Registros"):
            Otros_Registros.Otros_Registros(usuario, puesto)
        elif st.session_state.get("Bonos_Extras"):
            Bonos_Extras.Bonos_Extras(usuario, puesto)
        elif st.session_state.get("Correcciones"):
            Correcciones.Correcciones(usuario, puesto)
        elif st.session_state.get("Precampo_Juridico"):
            Precampo_Juridico.Precampo_Juridico(usuario, puesto)
        elif st.session_state.get("Descarga_Partidas_Juridico"):
            Descarga_Partidas_Juridico.Descarga_Partidas_Juridico(usuario, puesto)
        elif st.session_state.get("CC_Precampo_Juridico"):
            CC_Precampo_Juridico.CC_Precampo_Juridico(usuario, puesto)
        elif st.session_state.get("Asignacion_Partidas"):
            Asignacion_Partidas.Asignacion_Partidas(usuario, puesto)
        else:
            st.session_state.Procesos = False
            menu_principal_por_perfil(usuario, puesto, "3")
    else:
        menu_principal_por_perfil(usuario, puesto, "3")
