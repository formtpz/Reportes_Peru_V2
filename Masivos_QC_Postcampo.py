# ----- Librerías ---- #
import streamlit as st
from datetime import datetime
import pytz
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute


def Masivos_QC_Postcampo(usuario, puesto):

    # ----- Sidebar ----- #
    with st.sidebar:
        ph_sidebar = st.empty()

        with ph_sidebar.container():
            st.title("Menú")
            procesos_btn      = st.button("Procesos",       key="procesos_mqcp")
            historial_btn     = st.button("Historial",      key="historial_mqcp")
            capacitacion_btn  = st.button("Capacitaciones", key="capacitacion_mqcp")
            otros_registros_btn = st.button("Otros Registros", key="otros_registros_mqcp")
            bonos_extras_btn  = st.button("Bonos y Extras", key="bonos_extras_mqcp")
            salir_btn         = st.button("Salir",          key="salir_mqcp")

    # ----- Contenido Principal ----- #
    ph_main = st.empty()

    with ph_main.container():
        st.title(":blue[Masivos QC Postcampo]")

        # Fecha por defecto
        default_date = datetime.now(pytz.timezone('America/Guatemala'))
        fecha = st.date_input("Fecha", value=default_date, key="fecha_mqcp")

        distrito = st.selectbox(
            "Distrito",
            options=("Chorrillos", "San Juan De Miraflores", "Villa el Salvador"),
            key="distrito_mqcp"
        )

        # Mapeo de abreviatura según distrito
        abrev_distrito = {
            "Chorrillos": "CH",
            "San Juan De Miraflores": "SJM",
            "Villa el Salvador": "VES"
        }
        abrev = abrev_distrito[distrito]  # se usará para la observación

        tipo = st.selectbox(
            "Tipo",
            options=("Ordinario", "Producción Horas Extras"),
            key="tipo_mqcp"
        )

        tipo_de_masivo = st.multiselect(
            "Tipo de Masivo",
            options=(
                "Sin-Rentas",
                "UA-Rentas",
                "UAvsRentas",
                "No Código/No Partida",
                "Titulares",
                "Partidas"
            ),
            key="tipo_de_masivo_mqcp"
        )

        cantidad_masivos = st.number_input(
            "Cantidad de Masivos Revisados",
            min_value=0,
            step=1,
            key="cantidad_masivos_mqcp"
        )

        horas = st.number_input(
            "Cantidad de Horas Trabajadas en el Proceso",
            min_value=0.0,
            key="horas_mqcp"
        )

        # --- NUEVO: número para observación automática ---
        numero_obs = st.number_input(
            "Número de Polígono",
            min_value=0,
            max_value=99,
            step=1,
            format="%02d",          # muestra siempre dos dígitos (09, 99, etc.)
            key="numero_obs_mqcp"
        )

        # Previsualización de la observación que se guardará
        observacion = f"{abrev}{numero_obs:02d}"
        st.caption(f"📝 Polígono que se registrará: **{observacion}**")

        reporte_btn = st.button("Guardar Registro", key="reporte_mqcp")

    # ----- Navegación ----- #

    if procesos_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Procesos = True

        usuario_activo = obtener_usuario_activo(usuario)
        perfil = str(usuario_activo["perfil"]) if usuario_activo else ""

        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)

    elif historial_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_registros_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_extras_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_btn:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.Masivos_QC_Postcampo = False
        st.session_state.Ingreso = False
        st.session_state.Salir = True
        Salir.Salir()

    elif reporte_btn:
        marca = datetime.now(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")

        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo:
            st.error("No se encontró un usuario activo para generar el reporte.")
            return

        nombre     = usuario_activo["nombre"]
        supervisor = usuario_activo["supervisor"]

        semana   = fecha.isocalendar()[1]
        año      = fecha.isocalendar()[0]
        horas_bi = float(horas)

        tipos_de_masivo_str = ','.join(tipo_de_masivo)
        conteo              = len(tipo_de_masivo)

        # Valores fijos para este módulo
        operador_cc         = "N/A"
        aprobados           = 0
        rechazados          = 0
        unidades_catastrales = int(cantidad_masivos)

        execute(
            """
            INSERT INTO registro (
                marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
                distrito, tipo, lotes, aprobados, rechazados, horas,
                manzana, sector, numero_lote, estado, area, unidades_catastrales,
                edificas, partida, con_fmi, sin_fmi, observaciones, zona,
                tipo_calidad, horas_bi, area_bi, operador_cc, total_de_errores,
                errores_por_excepciones, tipo_de_errores, conteo_de_errores
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            params=[
                marca, usuario, nombre, puesto, supervisor, "Masivos QC Postcampo",
                fecha, semana, año, distrito, tipo, 0, aprobados, rechazados, horas,
                0, 0, "0",
                "N/A", 0.0, unidades_catastrales,
                0, "N/A", 0, 0, observacion,   # ¡Aquí va la observación generada!
                "N/A",
                "N/A", horas_bi, 0, operador_cc, 0,
                0, tipos_de_masivo_str, conteo
            ],
        )

        st.success("✅ Registro guardado correctamente")
