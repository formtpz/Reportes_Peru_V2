# ----- Librerías -----
import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

import Procesos, Historial, Capacitacion, Otros_Registros, Salir
from db_core import fetch_df, fetch_one

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------

def limpiar_placeholders(lista_placeholders):
    """Vacía todos los placeholders proporcionados."""
    for ph in lista_placeholders:
        if ph is not None:
            ph.empty()


def navegar_a_procesos(usuario, puesto):
    """Determina el perfil y redirige a la función correspondiente de Procesos."""
    perfil_info = fetch_one("SELECT perfil FROM usuarios WHERE usuario = %s", params=[usuario])
    perfil = str(perfil_info["perfil"]) if perfil_info else "1"
    if perfil == "1":
        Procesos.Procesos1(usuario, puesto)
    elif perfil == "2":
        Procesos.Procesos2(usuario, puesto)
    else:
        Procesos.Procesos3(usuario, puesto)


# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# -------------------------------------------------------------------

def Bonos_Extras(usuario, puesto):
    # Obtener datos del usuario
    usuario_info = fetch_one(
        "SELECT nombre, perfil FROM usuarios WHERE usuario = %s",
        params=[usuario]
    )
    nombre_9 = usuario_info["nombre"] if usuario_info else ""
    perfil_9 = str(usuario_info["perfil"]) if usuario_info else ""

    # --- Sidebar ---
    ph_sidebar = []
    ph_titulo = st.sidebar.empty()
    ph_titulo.title("Menú")
    ph_sidebar.append(ph_titulo)

    btn_procesos = st.sidebar.empty()
    ph_sidebar.append(btn_procesos)
    btn_historial = st.sidebar.empty()
    ph_sidebar.append(btn_historial)
    btn_capacitacion = st.sidebar.empty()
    ph_sidebar.append(btn_capacitacion)
    btn_otros = st.sidebar.empty()
    ph_sidebar.append(btn_otros)
    btn_salir = st.sidebar.empty()
    ph_sidebar.append(btn_salir)

    # --- Título principal ---
    ph_main = []
    titulo = st.empty()
    ph_main.append(titulo)
    titulo.title("Registros de Bonos y Horas Extra")

    # Lista para almacenar todos los placeholders de contenido dinámico
    placeholders_contenido = []

    # -------------------------------------------------------------------
    # RAMA ADMINISTRADORES (carga de archivos)
    # -------------------------------------------------------------------
    if nombre_9 in ["Brayan Rojas Pastrana", "Brandon Felipe Mata Ortega", "Evelyn Burgos Chavarria"]:
        ph_sub = st.empty()
        placeholders_contenido.append(ph_sub)
        with ph_sub.container():
            st.subheader("Archivos")

            ph_bloques = st.empty()
            placeholders_contenido.append(ph_bloques)
            bloques_nuevos = ph_bloques.file_uploader("Cargar Archivo de Bloques", ['csv', 'xlsx'], key="bloques")

            ph_bonos = st.empty()
            placeholders_contenido.append(ph_bonos)
            bonos_nuevos = ph_bonos.file_uploader("Cargar Archivo de Bonos", ['csv', 'xlsx'], key="bonos")

            ph_extras = st.empty()
            placeholders_contenido.append(ph_extras)
            extras_nuevas = ph_extras.file_uploader("Cargar Archivo de Extras", ['csv', 'xlsx'], key="extras")

            ph_unidades = st.empty()
            placeholders_contenido.append(ph_unidades)
            unidades_nuevas = ph_unidades.file_uploader("Cargar Archivo de Unidades Jurídicas", ['csv', 'xlsx'], key="unidades")

            ph_bonos_jur = st.empty()
            placeholders_contenido.append(ph_bonos_jur)
            bonos_juridico = ph_bonos_jur.file_uploader("Cargar Archivo de Bonos Jurídicos", ['csv', 'xlsx'], key="bonos_juridico")

            ph_btn_cargar = st.empty()
            placeholders_contenido.append(ph_btn_cargar)
            btn_cargar = ph_btn_cargar.button("Cargar Archivos", key="cargar_archivos")

            if btn_cargar:
                uri = st.secrets.db_credentials.URI
                engine = create_engine(uri)

                def cargar(uploaded_file, table_name):
                    if uploaded_file is not None:
                        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
                        df.to_sql(name=table_name, con=engine, if_exists='append', index=False)
                        st.success(f'Archivo "{table_name}" cargado correctamente')

                cargar(bloques_nuevos, 'bloques')
                cargar(bonos_nuevos, 'bonos')
                cargar(extras_nuevas, 'extras')
                cargar(unidades_nuevas, 'unidades')
                cargar(bonos_juridico, 'bonos_juridico')

                if all(f is None for f in [bloques_nuevos, bonos_nuevos, extras_nuevas, unidades_nuevas, bonos_juridico]):
                    st.warning("No se cargó ningún archivo.")

    # -------------------------------------------------------------------
    # RAMA SUPERVISORES (Gabriel/Madeline)
    # -------------------------------------------------------------------
    elif nombre_9 in ["Gabriel Martin Prieto", "Madeline Hernandez Gamboa"]:
        data_personal = fetch_df("SELECT nombre FROM usuarios WHERE estado = 'Activo'", params=[])
        todos_df = pd.DataFrame({"nombre": ["Todos"]})
        data_personal = pd.concat([data_personal, todos_df], ignore_index=True)

        ph_personal = st.empty()
        placeholders_contenido.append(ph_personal)
        with ph_personal.container():
            personal_sel = st.selectbox("Personal", data_personal, key="personal_9")

        periodos = ["Agosto-2025","Septiembre-2025","Octubre-2025","Noviembre-2025","Diciembre-2025",
                    "Enero-2026","Febrero-2026","Marzo-2026","Abril-2026","Mayo-2026","Junio-2026",
                    "Julio-2026","Agosto-2026","Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]
        ph_periodo = st.empty()
        placeholders_contenido.append(ph_periodo)
        with ph_periodo.container():
            periodo_sel = st.selectbox("Periodo de Bono", options=periodos, key="periodo_9")

        if personal_sel == "Todos":
            ph_bonos = st.empty()
            placeholders_contenido.append(ph_bonos)
            with ph_bonos.container():
                st.subheader("Bonos")
                bonos_df = fetch_df(
                    "SELECT a8, a15, a17, a18, a21, a16, a22 FROM bonos WHERE a23 = %s",
                    params=[periodo_sel]
                )
                if bonos_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    bono_prod = bonos_df['a8'].astype(float).sum()
                    bono_cal = bonos_df['a15'].astype(float).sum()
                    bono_sup = bonos_df['a17'].astype(float).sum()
                    bono_cal_ext = bonos_df['a18'].astype(float).sum()
                    bono_var = bonos_df['a21'].astype(float).sum()
                    bono_fijo = bonos_df['a16'].astype(float).sum()
                    bono_total = bonos_df['a22'].astype(float).sum()

                    cols = st.columns(7)
                    cols[0].metric("Bono Productividad", bono_prod)
                    cols[1].metric("Bono Calidad", bono_cal)
                    cols[2].metric("Bono Supervisión", bono_sup)
                    cols[3].metric("Bono Calidad Externa IGAC", bono_cal_ext)
                    cols[4].metric("Bono Variable", bono_var)
                    cols[5].metric("Bono Fijo", bono_fijo)
                    cols[6].metric("Bono Total", bono_total)

            ph_extras = st.empty()
            placeholders_contenido.append(ph_extras)
            with ph_extras.container():
                st.subheader("Horas Extra")
                # CORRECCIÓN: Mostrar todas las columnas como en el código viejo
                extras_df = fetch_df(
                    "SELECT marca, usuario, nombre, puesto, supervisor, tipo_reporte, justificacion, fecha, horas, semana, dia, fecha_corte, fecha_bono FROM extras WHERE tipo_reporte IN ('Extra','Horas Extra','Horas Extra Apoyo Otros Proyectos') AND fecha_bono = %s",
                    params=[periodo_sel]
                )
                if extras_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    total_extras = extras_df['horas'].astype(float).sum()
                    st.metric("Total de Horas Extra", total_extras)
                    st.dataframe(extras_df)

        else:
            ph_bonos = st.empty()
            placeholders_contenido.append(ph_bonos)
            with ph_bonos.container():
                st.subheader("Bonos")
                bonos_df = fetch_df(
                    "SELECT a8, a15, a17, a18, a21, a16, a22 FROM bonos WHERE a1 = %s AND a23 = %s",
                    params=[personal_sel, periodo_sel]
                )
                if bonos_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    fila = bonos_df.iloc[0]
                    bono_prod = float(fila['a8'])
                    bono_cal = float(fila['a15'])
                    bono_sup = float(fila['a17'])
                    bono_cal_ext = float(fila['a18'])
                    bono_var = float(fila['a21'])
                    bono_fijo = float(fila['a16'])
                    bono_total = float(fila['a22'])

                    cols = st.columns(7)
                    cols[0].metric("Bono Productividad", bono_prod)
                    cols[1].metric("Bono Calidad", bono_cal)
                    cols[2].metric("Bono Supervisión", bono_sup)
                    cols[3].metric("Bono Calidad Externa IGAC", bono_cal_ext)
                    cols[4].metric("Bono Variable", bono_var)
                    cols[5].metric("Bono Fijo", bono_fijo)
                    cols[6].metric("Bono Total", bono_total)

            ph_extras = st.empty()
            placeholders_contenido.append(ph_extras)
            with ph_extras.container():
                st.subheader("Horas Extra")
                # CORRECCIÓN: Mostrar todas las columnas como en el código viejo
                extras_df = fetch_df(
                    "SELECT marca, usuario, nombre, puesto, supervisor, tipo_reporte, justificacion, fecha, horas, semana, dia, fecha_corte, fecha_bono FROM extras WHERE nombre = %s AND tipo_reporte IN ('Extra','Horas Extra','Horas Extra Apoyo Otros Proyectos') AND fecha_bono = %s",
                    params=[personal_sel, periodo_sel]
                )
                if extras_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    total_extras = extras_df['horas'].astype(float).sum()
                    st.metric("Total de Horas Extra", total_extras)
                    st.dataframe(extras_df)

    # -------------------------------------------------------------------
    # RAMA IGNACIO (Jurídico)
    # -------------------------------------------------------------------
    elif nombre_9 == "Ignacio Aguglino":
        data_personal = fetch_df("SELECT nombre FROM usuarios WHERE puesto = 'Profesional Jurídico' AND estado = 'Activo'", params=[])
        todos_df = pd.DataFrame({"nombre": ["Todos"]})
        data_personal = pd.concat([data_personal, todos_df], ignore_index=True)

        ph_personal = st.empty()
        placeholders_contenido.append(ph_personal)
        with ph_personal.container():
            personal_sel = st.selectbox("Personal", data_personal, key="personal_9")

        periodos = ["Agosto-2025","Septiembre-2025","Octubre-2025","Noviembre-2025","Diciembre-2025",
                    "Enero-2026","Febrero-2026","Marzo-2026","Abril-2026","Mayo-2026","Junio-2026",
                    "Julio-2026","Agosto-2026","Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]
        ph_periodo = st.empty()
        placeholders_contenido.append(ph_periodo)
        with ph_periodo.container():
            periodo_sel = st.selectbox("Periodo de Bono", options=periodos, key="periodo_9")

        if personal_sel == "Todos":
            ph_bonos = st.empty()
            placeholders_contenido.append(ph_bonos)
            with ph_bonos.container():
                st.subheader("Bonos")
                bonos_jur_df = fetch_df(
                    "SELECT a23 FROM bonos_juridico WHERE a24 = %s",
                    params=[periodo_sel]
                )
                if bonos_jur_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    total = pd.to_numeric(bonos_jur_df['a23']).sum()
                    st.metric("Total Bonos Jurídicos (COP)", value=total)
        else:
            ph_bonos = st.empty()
            placeholders_contenido.append(ph_bonos)
            with ph_bonos.container():
                st.subheader("Bonos")
                bonos_jur_df = fetch_df(
                    "SELECT * FROM bonos_juridico WHERE a0 = %s AND a24 = %s",
                    params=[personal_sel, periodo_sel]
                )
                if bonos_jur_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    fila = bonos_jur_df.iloc[0]
                    data_procesos = {
                        "Variables": ["Producción (Según Reportes)","Producción (Limpia)","Producción (Estándar)","Bono (COP)", "Bonificación Otras Funciones (COP)", "Observaciones", "Bonificación Total (COP)"],
                        "Folios de Matricula Inmobiliaria": [fila['a4'], fila['a8'], fila['a12'], fila['a16'], fila['a20'], fila['a22'], fila['a23']],
                        "CC Folios de Matricula Inmobiliaria": [fila['a5'], fila['a9'], fila['a13'], fila['a17'], " ", " ", " "],
                        "Consultas de Campo": [fila['a6'], fila['a10'], fila['a14'], fila['a18'], " ", " ", " "]
                    }
                    st.dataframe(pd.DataFrame(data_procesos))

            ph_unidades = st.empty()
            placeholders_contenido.append(ph_unidades)
            with ph_unidades.container():
                st.subheader("Unidades de Asignación")
                periodo_bloques = st.selectbox("Fecha de Producción", options=["Todos"] + periodos, key="periodo_bloques")
                if periodo_bloques == "Todos":
                    unidades_df = fetch_df(
                        "SELECT nombre, supervisor, proceso, unidad_asignacion, tipo_revision, produccion_segun_reporte, produccion_rechazada_primera_revision, produccion_aprobada_primera_revision, porcentage_error, produccion_penalizada, produccion_limpia, fecha_produccion, fecha_bono FROM unidades WHERE nombre = %s",
                        params=[personal_sel]
                    )
                else:
                    unidades_df = fetch_df(
                        "SELECT nombre, supervisor, proceso, unidad_asignacion, tipo_revision, produccion_segun_reporte, produccion_rechazada_primera_revision, produccion_aprobada_primera_revision, porcentage_error, produccion_penalizada, produccion_limpia, fecha_produccion, fecha_bono FROM unidades WHERE nombre = %s AND fecha_produccion = %s",
                        params=[personal_sel, periodo_bloques]
                    )
                if unidades_df.empty:
                    st.error("No existen datos para mostrar")
                else:
                    st.dataframe(unidades_df)

    # -------------------------------------------------------------------
    # RAMA PERFIL 2 o 1 (Operadores / Supervisores genéricos)
    # -------------------------------------------------------------------
    elif perfil_9 in ["1", "2"]:
        periodos = ["Agosto-2025","Septiembre-2025","Octubre-2025","Noviembre-2025","Diciembre-2025",
                    "Enero-2026","Febrero-2026","Marzo-2026","Abril-2026","Mayo-2026","Junio-2026",
                    "Julio-2026","Agosto-2026","Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]
        ph_periodo = st.empty()
        placeholders_contenido.append(ph_periodo)
        with ph_periodo.container():
            periodo_sel = st.selectbox("Periodo", options=periodos, key="periodo_bonos_9")

        ph_bonos = st.empty()
        placeholders_contenido.append(ph_bonos)
        with ph_bonos.container():
            # CORRECCIÓN: Usar las columnas correctas como en el código viejo
            bonos_df = fetch_df(
                "SELECT a5, a6, a7, a8, a9, a10, a17, a18, a19, a20, a21, a22 FROM bonos WHERE a0 = %s AND a23 = %s",
                params=[usuario, periodo_sel]
            )
            if bonos_df.empty:
                st.error("No existen datos para mostrar")
            else:
                fila = bonos_df.iloc[0]
                # Mapeo correcto según el código viejo
                bono_productividad_precampo = float(fila['a5']) if pd.notna(fila['a5']) else 0.0
                bono_calidad_precampo = float(fila['a6']) if pd.notna(fila['a6']) else 0.0
                bono_productividad_postcampo = float(fila['a7']) if pd.notna(fila['a7']) else 0.0
                bono_calidad_postcampo = float(fila['a8']) if pd.notna(fila['a8']) else 0.0
                bono_productividad_vinculacion = float(fila['a9']) if pd.notna(fila['a9']) else 0.0
                bono_calidad_vinculacion = float(fila['a10']) if pd.notna(fila['a10']) else 0.0
                bono_supervision = float(fila['a17']) if pd.notna(fila['a17']) else 0.0
                bonos_entregas = float(fila['a18']) if pd.notna(fila['a18']) else 0.0
                bono_calidad_externa = float(fila['a19']) if pd.notna(fila['a19']) else 0.0
                bonos_fijos = float(fila['a20']) if pd.notna(fila['a20']) else 0.0
                bonos_otro_proyecto = float(fila['a21']) if pd.notna(fila['a21']) else 0.0
                bono_total = float(fila['a22']) if pd.notna(fila['a22']) else 0.0
                
                df_bonos = pd.DataFrame({
                    "Concepto": [
                        "Bono Productividad (Precampo)",
                        "Bono Calidad (Precampo)",
                        "Bono Productividad (Postcampo)",
                        "Bono Calidad (Postcampo)",
                        "Bono Productividad (Vinculación)",
                        "Bono Calidad (Vinculación)",
                        "Bono Supervisión",
                        "Bono Entregas",
                        "Bono Calidad Externa",
                        "Bono Fijo",
                        "Bono Otro Proyecto",
                        "TOTAL"
                    ],
                    "Monto de bonificación": [
                        bono_productividad_precampo,
                        bono_calidad_precampo,
                        bono_productividad_postcampo,
                        bono_calidad_postcampo,
                        bono_productividad_vinculacion,
                        bono_calidad_vinculacion,
                        bono_supervision,
                        bonos_entregas,
                        bono_calidad_externa,
                        bonos_fijos,
                        bonos_otro_proyecto,
                        bono_total
                    ]
                })
                st.dataframe(df_bonos, hide_index=True, height=460)

        ph_extras = st.empty()
        placeholders_contenido.append(ph_extras)
        with ph_extras.container():
            st.subheader("Horas Extras")
            # CORRECCIÓN: Mostrar todas las columnas como en el código viejo
            extras_df = fetch_df(
                "SELECT marca, usuario, nombre, puesto, supervisor, tipo_reporte, justificacion, fecha, horas, semana, dia, fecha_corte, fecha_bono FROM extras WHERE nombre = %s AND tipo_reporte IN ('Extra','Horas Extra','Horas Extra Apoyo Otros Proyectos') AND fecha_bono = %s",
                params=[nombre_9, periodo_sel]
            )
            if extras_df.empty:
                st.error("No existen datos para mostrar")
            else:
                total_extras = extras_df['horas'].astype(float).sum()
                st.metric("Total de Horas Extra", total_extras)
                st.dataframe(extras_df)

    # -------------------------------------------------------------------
    # RAMA PERFIL 3 (Jurídicos)
    # -------------------------------------------------------------------
    elif perfil_9 == "3":
        periodos = ["Agosto-2025","Septiembre-2025","Octubre-2025","Noviembre-2025","Diciembre-2025",
                    "Enero-2026","Febrero-2026","Marzo-2026","Abril-2026","Mayo-2026","Junio-2026",
                    "Julio-2026","Agosto-2026","Septiembre-2026","Octubre-2026","Noviembre-2026","Diciembre-2026"]
        ph_periodo = st.empty()
        placeholders_contenido.append(ph_periodo)
        with ph_periodo.container():
            periodo_sel = st.selectbox("Periodo", options=periodos, key="periodo_bonos_9")

        ph_extras = st.empty()
        placeholders_contenido.append(ph_extras)
        with ph_extras.container():
            st.subheader("Horas Extras")
            # CORRECCIÓN: Mostrar todas las columnas como en el código viejo
            extras_df = fetch_df(
                "SELECT marca, usuario, nombre, puesto, supervisor, tipo_reporte, justificacion, fecha, horas, semana, dia, fecha_corte, fecha_bono FROM extras WHERE nombre = %s AND tipo_reporte IN ('Extra','Horas Extra','Horas Extra Apoyo Otros Proyectos') AND fecha_bono = %s",
                params=[nombre_9, periodo_sel]
            )
            if extras_df.empty:
                st.error("No existen datos para mostrar")
            else:
                total_extras = extras_df['horas'].astype(float).sum()
                st.metric("Total de Horas Extra", total_extras)
                st.dataframe(extras_df)

    # -------------------------------------------------------------------
    # NAVEGACIÓN
    # -------------------------------------------------------------------
    def limpiar_todo():
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)

    if btn_procesos.button("Procesos", key="procesos_9"):
        limpiar_todo()
        st.session_state.Bonos_Extras = False
        navegar_a_procesos(usuario, puesto)

    elif btn_historial.button("Historial", key="historial_9"):
        limpiar_todo()
        st.session_state.Bonos_Extras = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif btn_capacitacion.button("Capacitaciones", key="capacitacion_9"):
        limpiar_todo()
        st.session_state.Bonos_Extras = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif btn_otros.button("Otros Registros", key="otros_registros_9"):
        limpiar_todo()
        st.session_state.Bonos_Extras = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif btn_salir.button("Salir", key="salir_9"):
        limpiar_todo()
        st.session_state.Ingreso = False
        st.session_state.Bonos_Extras = False
        st.session_state.Salir = True
        Salir.Salir()
