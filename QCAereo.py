# ----- Librerías ---- #
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute


def QCAereo(usuario, puesto):

    # ----- Sidebar ----- #
    placeholder1_4 = st.sidebar.empty()
    placeholder1_4.title("Menú")

    placeholder2_4 = st.sidebar.empty()
    procesos_4 = placeholder2_4.button("Procesos", key="procesos_4")

    placeholder3_4 = st.sidebar.empty()
    historial_4 = placeholder3_4.button("Historial", key="historial_4")

    placeholder4_4 = st.sidebar.empty()
    capacitacion_4 = placeholder4_4.button("Capacitaciones", key="capacitacion_4")

    placeholder5_4 = st.sidebar.empty()
    otros_registros_4 = placeholder5_4.button("Otros Registros", key="otros_registros_4")

    placeholder6_4 = st.sidebar.empty()
    bonos_extras_4 = placeholder6_4.button("Bonos y Horas Extras", key="bonos_extras_4")

    placeholder7_4 = st.sidebar.empty()
    salir_4 = placeholder7_4.button("Salir", key="salir_4")

    # ----- Contenido principal ----- #
    placeholder8_4 = st.empty()
    placeholder8_4.title("QC Aéreo")

    default_date_4 = datetime.now(pytz.timezone('America/Guatemala'))

    placeholder9_4 = st.empty()
    fecha_4 = placeholder9_4.date_input("Fecha", value=default_date_4, key="fecha_4")

    placeholder10_4 = st.empty()
    distrito_4 = placeholder10_4.selectbox(
        "Distrito",
        options=("Chorrillos", "San Juan De Miraflores", "Villa el Salvador"),
        key="distrito_4"
    )

    placeholder11_4 = st.empty()
    sector_4 = placeholder11_4.selectbox(
        "Sector",
        options=tuple(f"{i:02d}" for i in range(1, 121)),   # "01" ... "120"
        key="sector_4"
    )

    placeholder12_4 = st.empty()
    manzana_4 = placeholder12_4.selectbox(
        "Manzana",
        options=tuple(f"{i:03d}" for i in range(1, 121)),   # "001" ... "120"
        key="manzana_4"
    )

    placeholder13_4 = st.empty()
    poligono_4 = placeholder13_4.text_input(
        "Polígono",
        max_chars=60,
        key="poligono_4"
    )

    placeholder14_4 = st.empty()
    tipo_4 = placeholder14_4.selectbox(
        "Tipo",
        options=("Ordinario", "Producción Horas Extras"),
        key="tipo_4"
    )

    placeholder15_4 = st.empty()
    lotes_inspeccionados_4 = placeholder15_4.number_input(
        "Número de Lotes Inspeccionados",
        min_value=0,
        step=1,
        key="lotes_inspeccionados_4"
    )

    placeholder16_4 = st.empty()
    unidades_catastrales_4 = placeholder16_4.number_input(
        "Cantidad de Unidades Catastrales",
        min_value=0,
        step=1,
        key="unidades_catastrales_4"
    )

    placeholder17_4 = st.empty()
    horas_4 = placeholder17_4.number_input(
        "Cantidad de Horas Trabajadas en el Proceso",
        min_value=0.0,
        key="horas_4"
    )

    placeholder18_4 = st.empty()
    observaciones_4 = placeholder18_4.text_input(
        "Observaciones",
        value="N/A",
        max_chars=60,
        key="observaciones_4"
    )

    placeholder19_4 = st.empty()
    reporte_4 = placeholder19_4.button("Generar Reporte", key="reporte_4")

    # Lista completa para limpiar al navegar
    todos_placeholders = [
        placeholder1_4, placeholder2_4, placeholder3_4, placeholder4_4,
        placeholder5_4, placeholder6_4, placeholder7_4, placeholder8_4,
        placeholder9_4, placeholder10_4, placeholder11_4, placeholder12_4,
        placeholder13_4, placeholder14_4, placeholder15_4, placeholder16_4,
        placeholder17_4, placeholder18_4, placeholder19_4,
    ]

    def limpiar_todo():
        for ph in todos_placeholders:
            ph.empty()

    # ----- Navegación ----- #
    if procesos_4:
        limpiar_todo()
        st.session_state.QCAereo = False
        usuario_activo = obtener_usuario_activo(usuario)
        perfil = str(usuario_activo["perfil"]) if usuario_activo else ""
        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)

    elif historial_4:
        limpiar_todo()
        st.session_state.QCAereo = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_4:
        limpiar_todo()
        st.session_state.QCAereo = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_registros_4:
        limpiar_todo()
        st.session_state.QCAereo = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_extras_4:
        limpiar_todo()
        st.session_state.QCAereo = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_4:
        limpiar_todo()
        st.session_state.Ingreso = False
        st.session_state.QCAereo = False
        st.session_state.Salir = True
        Salir.Salir()

    # ----- Generar Reporte ----- #
    elif reporte_4:
        marca_4 = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")

        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo:
            st.error("No se encontró un usuario activo para generar el reporte.")
            return

        nombre_4     = usuario_activo["nombre"]
        supervisor_4 = usuario_activo["supervisor"]
        semana_4     = fecha_4.isocalendar()[1]
        año_4        = fecha_4.isocalendar()[0]
        horas_bi     = float(horas_4)

        # Observaciones: N/A si el usuario no escribe nada
        obs_final = observaciones_4.strip() if observaciones_4 and observaciones_4.strip() else "N/A"

        execute(
            """
            INSERT INTO registro (
                marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
                distrito, tipo, lotes, aprobados, rechazados, horas, manzana, sector,
                numero_lote, estado, area, unidades_catastrales, edificas, partida,
                con_fmi, sin_fmi, observaciones, zona, tipo_calidad, horas_bi, area_bi,
                operador_cc, total_de_errores, errores_por_excepciones, tipo_de_errores,
                conteo_de_errores
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s
            )
            """,
            params=[
                marca_4, usuario, nombre_4, puesto, supervisor_4, "QC Aereo", fecha_4, semana_4, año_4,
                distrito_4, tipo_4, int(lotes_inspeccionados_4), 0, 0, horas_4, manzana_4, sector_4,
                "0", "N/A", 0.0, unidades_catastrales_4, 0, poligono_4,
                0, 0, obs_final, "N/A", "N/A", horas_bi, 0.0,
                "N/A", 0, 0, "N/A",
                0
            ],
        )
        st.success('Reporte enviado correctamente')
