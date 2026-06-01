# ----- Librerías ---- #
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

import Procesos, Historial, Otros_Registros, Bonos_Extras, Salir
from db_core import fetch_df, fetch_one, execute


def limpiar_placeholders(lista_placeholders):
    for ph in lista_placeholders:
        if ph is not None:
            ph.empty()


def navegar_a_procesos(usuario, puesto):
    """Redirige a Procesos según perfil del usuario."""
    perfil_info = fetch_one("SELECT perfil FROM usuarios WHERE usuario = %s", params=[usuario])
    perfil = str(perfil_info["perfil"]) if perfil_info else "1"
    if perfil == "1":
        Procesos.Procesos1(usuario, puesto)
    elif perfil == "2":
        Procesos.Procesos2(usuario, puesto)
    else:
        Procesos.Procesos3(usuario, puesto)


def Capacitacion(usuario, puesto):
    # Obtener nombre completo del usuario
    nombre_df = fetch_df("SELECT nombre FROM usuarios WHERE usuario = %s", params=[usuario])
    nombre_usuario = nombre_df.loc[0, 'nombre'] if not nombre_df.empty else ""

    # --- Sidebar (común a todos los perfiles) ---
    ph_sidebar = []
    ph_titulo = st.sidebar.empty()
    ph_titulo.title("Menú")
    ph_sidebar.append(ph_titulo)

    btn_procesos = st.sidebar.empty()
    ph_sidebar.append(btn_procesos)
    btn_historial = st.sidebar.empty()
    ph_sidebar.append(btn_historial)
    btn_otros = st.sidebar.empty()
    ph_sidebar.append(btn_otros)
    btn_bonos = st.sidebar.empty()
    ph_sidebar.append(btn_bonos)
    btn_salir = st.sidebar.empty()
    ph_sidebar.append(btn_salir)

    # --- Contenido principal (depende del perfil) ---
    ph_main = []
    titulo = st.empty()
    ph_main.append(titulo)
    titulo.title("Capacitaciones")

    # Fecha por defecto para filtros
    default_date = datetime.now(pytz.timezone('America/Guatemala'))

    # Variables que se usarán en los if de navegación
    data = pd.DataFrame()
    placeholders_contenido = []

    # Placeholder para mensajes (se crea una vez y se reutiliza)
    ph_mensaje = st.empty()
    placeholders_contenido.append(ph_mensaje)

    # =========================================================
    # COORDINADOR
    # =========================================================
    if puesto == "Coordinador":
        # --- Registro de capacitación ---
        ph_registro = st.empty()
        placeholders_contenido.append(ph_registro)
        ph_registro.subheader("Registro")

        # Cargar lista de personal activo
        df_personal = fetch_df("SELECT nombre FROM usuarios WHERE estado = 'Activo'")
        personal_opciones = df_personal["nombre"].tolist() if not df_personal.empty else []

        ph_personal = st.empty()
        placeholders_contenido.append(ph_personal)
        personal_sel = ph_personal.multiselect("Personal", personal_opciones, key="personal_8")

        ph_fecha = st.empty()
        placeholders_contenido.append(ph_fecha)
        fecha_val = ph_fecha.date_input("Fecha", value=default_date, key="fecha_8")

        ph_tema = st.empty()
        placeholders_contenido.append(ph_tema)
        tema_val = ph_tema.selectbox(
            "Tema",
            options=("Bonos", "Información General", "Precampo", "QC Precampo", "Postcampo",
                     "QC Postcampo", "QGIS", "Reportes y Registros", "Sistema de Gestión Empresarial", "Otros"),
            key="tema_8"
        )

        ph_obs = st.empty()
        placeholders_contenido.append(ph_obs)
        obs_val = ph_obs.text_input("Observaciones", max_chars=60, key="observaciones_8")

        ph_horas = st.empty()
        placeholders_contenido.append(ph_horas)
        horas_val = ph_horas.number_input("Cantidad de Horas de Capacitación Individuales", min_value=0.0, key="horas_8")

        ph_reporte_btn = st.empty()
        placeholders_contenido.append(ph_reporte_btn)
        reporte_btn = ph_reporte_btn.button("Generar Reporte", key="reporte_8")

        ph_sep = st.empty()
        placeholders_contenido.append(ph_sep)
        ph_sep.markdown("_____")

        # --- Historial de capacitaciones ---
        ph_hist_titulo = st.empty()
        placeholders_contenido.append(ph_hist_titulo)
        ph_hist_titulo.subheader("Historial Capacitaciones")

        ph_fecha_ini = st.empty()
        placeholders_contenido.append(ph_fecha_ini)
        fecha_ini = ph_fecha_ini.date_input("Fecha de Inicio", value=default_date, key="fecha_inicio_8")

        ph_fecha_fin = st.empty()
        placeholders_contenido.append(ph_fecha_fin)
        fecha_fin = ph_fecha_fin.date_input("Fecha de Finalización", value=default_date, key="fecha_fin_8")

        ph_filtro = st.empty()
        placeholders_contenido.append(ph_filtro)
        filtro_val = ph_filtro.selectbox(
            "Filtro",
            options=("Todos", "Operarios", "Profesional Jurídico", "Propio", "Personal Asignado", "Reportados"),
            key="filtro_8"
        )

        # Cargar datos según filtro
        if filtro_val == "Todos":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Operarios":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE puesto = 'Operario Catastral' AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Profesional Jurídico":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE puesto = 'Profesional Jurídico' AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Propio":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[usuario, fecha_ini, fecha_fin]
            )
        elif filtro_val == "Personal Asignado":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE supervisor = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[nombre_usuario, fecha_ini, fecha_fin]
            )
        elif filtro_val == "Reportados":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE reporte = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[nombre_usuario, fecha_ini, fecha_fin]
            )

        ph_dataframe = st.empty()
        placeholders_contenido.append(ph_dataframe)
        ph_dataframe.dataframe(data)

        # --- Lógica del botón Generar Reporte ---
        if reporte_btn:
            if not personal_sel:
                ph_mensaje.error("Favor ingresar el nombre de alguna persona")
            else:
                try:
                    marca = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
                    for nombre in personal_sel:
                        # Obtener datos del usuario
                        user_info = fetch_one(
                            """
                            SELECT usuario, puesto, supervisor
                            FROM usuarios
                            WHERE nombre = %s
                            """,
                            params=[nombre]
                        )
                        if user_info:
                            execute(
                                """
                                INSERT INTO capacitaciones
                                    (marca, usuario, nombre, puesto, supervisor, fecha, tema, horas, observaciones, reporte)
                                VALUES
                                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                params=[
                                    marca,
                                    user_info["usuario"],
                                    nombre,
                                    user_info["puesto"],
                                    user_info["supervisor"],
                                    fecha_val,
                                    tema_val,
                                    horas_val,
                                    obs_val,
                                    nombre_usuario
                                ]
                            )
                    ph_mensaje.success("✅ Registro enviado correctamente")
                except Exception as e:
                    ph_mensaje.error(f"❌ Error al guardar: {str(e)}")

    # =========================================================
    # SUPERVISOR
    # =========================================================
    elif puesto == "Supervisor":
        ph_registro = st.empty()
        placeholders_contenido.append(ph_registro)
        ph_registro.subheader("Registro")

        # Personal asignado al supervisor + el mismo supervisor
        df_personal = fetch_df(
            """
            SELECT nombre FROM usuarios
            WHERE estado = 'Activo' AND (supervisor = %s OR usuario = %s)
            """,
            params=[nombre_usuario, usuario]
        )
        personal_opciones = df_personal["nombre"].tolist() if not df_personal.empty else []

        ph_personal = st.empty()
        placeholders_contenido.append(ph_personal)
        personal_sel = ph_personal.multiselect("Personal", personal_opciones, key="personal_8")

        ph_fecha = st.empty()
        placeholders_contenido.append(ph_fecha)
        fecha_val = ph_fecha.date_input("Fecha", value=default_date, key="fecha_8")

        ph_tema = st.empty()
        placeholders_contenido.append(ph_tema)
        tema_val = ph_tema.selectbox(
            "Tema",
            options=("Bonos", "Criterios Técnicos", "Información General", "QGIS",
                     "Reportes y Registros", "Sistema de Gestión Empresarial", "Otros"),
            key="tema_8"
        )

        ph_obs = st.empty()
        placeholders_contenido.append(ph_obs)
        obs_val = ph_obs.text_input("Observaciones", max_chars=60, key="observaciones_8")

        ph_horas = st.empty()
        placeholders_contenido.append(ph_horas)
        horas_val = ph_horas.number_input("Cantidad de Horas de Capacitación Individuales", min_value=0.0, key="horas_8")

        ph_reporte_btn = st.empty()
        placeholders_contenido.append(ph_reporte_btn)
        reporte_btn = ph_reporte_btn.button("Generar Reporte", key="reporte_8")

        ph_sep = st.empty()
        placeholders_contenido.append(ph_sep)
        ph_sep.markdown("_____")

        ph_hist_titulo = st.empty()
        placeholders_contenido.append(ph_hist_titulo)
        ph_hist_titulo.subheader("Historial")

        ph_fecha_ini = st.empty()
        placeholders_contenido.append(ph_fecha_ini)
        fecha_ini = ph_fecha_ini.date_input("Fecha de Inicio", value=default_date, key="fecha_inicio_8")

        ph_fecha_fin = st.empty()
        placeholders_contenido.append(ph_fecha_fin)
        fecha_fin = ph_fecha_fin.date_input("Fecha de Finalización", value=default_date, key="fecha_fin_8")

        ph_filtro = st.empty()
        placeholders_contenido.append(ph_filtro)
        filtro_val = ph_filtro.selectbox(
            "Filtro",
            options=("Todos", "Operarios", "Personal Jurídico", "Propio", "Personal Asignado", "Reportados"),
            key="filtro_8"
        )

        # Cargar datos según filtro
        if filtro_val == "Todos":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Operarios":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE puesto = 'Operario Catastral' AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Personal Jurídico":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE puesto = 'Profesional Jurídico' AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[fecha_ini, fecha_fin]
            )
        elif filtro_val == "Propio":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[usuario, fecha_ini, fecha_fin]
            )
        elif filtro_val == "Personal Asignado":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE supervisor = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[nombre_usuario, fecha_ini, fecha_fin]
            )
        elif filtro_val == "Reportados":
            data = fetch_df(
                """
                SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                       fecha, tema, horas, observaciones, reporte
                FROM capacitaciones
                WHERE reporte = %s AND fecha::date >= %s AND fecha::date <= %s
                ORDER BY fecha DESC
                """,
                params=[nombre_usuario, fecha_ini, fecha_fin]
            )

        ph_dataframe = st.empty()
        placeholders_contenido.append(ph_dataframe)
        ph_dataframe.dataframe(data)

        # Botón Generar Reporte
        if reporte_btn:
            if not personal_sel:
                ph_mensaje.error("Favor ingresar el nombre de alguna persona")
            else:
                try:
                    marca = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
                    for nombre in personal_sel:
                        user_info = fetch_one(
                            """
                            SELECT usuario, puesto, supervisor
                            FROM usuarios
                            WHERE nombre = %s
                            """,
                            params=[nombre]
                        )
                        if user_info:
                            execute(
                                """
                                INSERT INTO capacitaciones
                                    (marca, usuario, nombre, puesto, supervisor, fecha, tema, horas, observaciones, reporte)
                                VALUES
                                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                params=[
                                    marca,
                                    user_info["usuario"],
                                    nombre,
                                    user_info["puesto"],
                                    user_info["supervisor"],
                                    fecha_val,
                                    tema_val,
                                    horas_val,
                                    obs_val,
                                    nombre_usuario
                                ]
                            )
                    ph_mensaje.success("✅ Registro enviado correctamente")
                except Exception as e:
                    ph_mensaje.error(f"❌ Error al guardar: {str(e)}")

    # =========================================================
    # OPERARIO / PROFESIONAL JURÍDICO / QC
    # =========================================================
    else:
        ph_hist_titulo = st.empty()
        placeholders_contenido.append(ph_hist_titulo)
        ph_hist_titulo.subheader("Historial")

        ph_fecha_ini = st.empty()
        placeholders_contenido.append(ph_fecha_ini)
        fecha_ini = ph_fecha_ini.date_input("Fecha de Inicio", value=default_date, key="fecha_inicio_8")

        ph_fecha_fin = st.empty()
        placeholders_contenido.append(ph_fecha_fin)
        fecha_fin = ph_fecha_fin.date_input("Fecha de Finalización", value=default_date, key="fecha_fin_8")

        data = fetch_df(
            """
            SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor,
                   fecha, tema, horas, observaciones, reporte
            FROM capacitaciones
            WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
            ORDER BY fecha DESC
            """,
            params=[usuario, fecha_ini, fecha_fin]
        )

        ph_dataframe = st.empty()
        placeholders_contenido.append(ph_dataframe)
        ph_dataframe.dataframe(data)

    # =========================================================
    # NAVEGACIÓN (común a todos los perfiles)
    # =========================================================
    if btn_procesos.button("Procesos", key="procesos_8"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Capacitacion = False
        navegar_a_procesos(usuario, puesto)

    elif btn_historial.button("Historial", key="historial_8"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Capacitacion = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif btn_otros.button("Otros Registros", key="otros_registros_8"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Capacitacion = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif btn_bonos.button("Bonos y Horas Extras", key="bonos_extra_8"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Capacitacion = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif btn_salir.button("Salir", key="salir_8"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Ingreso = False
        st.session_state.Capacitacion = False
        st.session_state.Salir = True
        Salir.Salir()
