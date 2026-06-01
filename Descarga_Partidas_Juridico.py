# ----- Librerías ---- #
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute


def Descarga_Partidas_Juridico(usuario, puesto):

    # ----- Sidebar fijo -----
    placeholder1_3 = st.sidebar.empty()
    placeholder1_3.title("Menú")

    placeholder2_3 = st.sidebar.empty()
    procesos_3 = placeholder2_3.button("Procesos", key="procesos_3")

    placeholder3_3 = st.sidebar.empty()
    historial_3 = placeholder3_3.button("Historial", key="historial_3")

    placeholder4_3 = st.sidebar.empty()
    capacitacion_3 = placeholder4_3.button("Capacitaciones", key="capacitacion_3")

    placeholder5_3 = st.sidebar.empty()
    otros_registros_3 = placeholder5_3.button("Otros Registros", key="otros_registros_3")

    placeholder6_3 = st.sidebar.empty()
    bonos_extras_3 = placeholder6_3.button("Bonos y Horas Extras", key="bonos_extras_3")

    placeholder7_3 = st.sidebar.empty()
    salir_3 = placeholder7_3.button("Salir", key="salir_3")

    # ----- Formulario (usando placeholders para limpiarlos después) -----
    placeholder8_3 = st.empty()
    placeholder8_3.title("Descarga Partidas Jurídico")

    default_date_3 = datetime.now(pytz.timezone('America/Guatemala'))

    placeholder9_3 = st.empty()
    fecha_3 = placeholder9_3.date_input("Fecha", value=default_date_3, key="fecha_3")

    placeholder10_3 = st.empty()
    distrito_3 = placeholder10_3.selectbox("Distrito", options=("Chorrillos", "San Juan De Miraflores", "Villa el Salvador"), key="distrito_3")

    placeholder12_3 = st.empty()
    sector_3 = placeholder12_3.selectbox("Sector", options=[f"{i:02d}" for i in range(1, 121)], key="sector_3")

    # Manzana en placeholder13_3
    placeholder13_3 = st.empty()
    manzana_3 = placeholder13_3.selectbox("Manzana", options=[f"{i:03d}" for i in range(1, 121)], key="manzana_3")

    placeholder15_3 = st.empty()
    tipo_3 = placeholder15_3.selectbox("Tipo", options=("Ordinario", "Reproceso Ordinario", "Corrección de Calidad", "Corrección de Calidad Extraordinaria", "Producción Horas Extras"), key="tipo_3")

    placeholder16_3 = st.empty()
    estado_3 = placeholder16_3.selectbox("Estado", options=("Finalizado", "En Conflicto"), key="estado_3")

    # Multiselect de lotes en placeholder18_3 (nuevo)
    lotes = ["Todos"] + [f"{i:03d}" for i in range(1, 249)]
    placeholder18_3 = st.empty()
    numero_lote_3 = placeholder18_3.multiselect(
        "Número de Lote",
        options=lotes,
        key="numero_lote_3"
    )
    if "Todos" in numero_lote_3:
        numero_lote_3 = ["Todos"]
    numero_lote_3 = ",".join(numero_lote_3)

    placeholder19_3 = st.empty()
    partida_3 = placeholder19_3.text_input("Número de Partida", value="N/A", max_chars=60, key="partida_3")

    placeholder20_3 = st.empty()
    unidades_catastrales_3 = placeholder20_3.number_input("Cantidad de Registros", min_value=0, step=1, key="unidades_catastrales_3")

    placeholder21_3 = st.empty()
    horas_3 = placeholder21_3.number_input("Cantidad de Horas Trabajadas en el Proceso", min_value=0.0, key="horas_3")

    placeholder22_3 = st.empty()
    observaciones_3 = placeholder22_3.text_input("Observaciones", value="N/A", max_chars=60, key="observaciones_3")

    placeholder23_3 = st.empty()
    reporte_3 = placeholder23_3.button("Generar Reporte", key="reporte_3")

    # ----- Navegación -----
    if procesos_3:
        # Limpiar todos los placeholders
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()

        st.session_state.Procesos = False
        st.session_state.Postcampo = False  # ajustar según el módulo activo

        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo or 'perfil' not in usuario_activo:
            st.error("Sesión inválida o expirada.")
            st.stop()
        perfil = str(usuario_activo["perfil"])

        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)

    elif historial_3:
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()
        st.session_state.Postcampo = False  # ajustar
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_3:
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()
        st.session_state.Postcampo = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_registros_3:
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()
        st.session_state.Postcampo = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_extras_3:
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()
        st.session_state.Postcampo = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_3:
        for p in [placeholder1_3, placeholder2_3, placeholder3_3, placeholder4_3,
                  placeholder5_3, placeholder6_3, placeholder7_3, placeholder8_3,
                  placeholder9_3, placeholder10_3, placeholder12_3, placeholder13_3,
                  placeholder15_3, placeholder16_3, placeholder18_3, placeholder19_3,
                  placeholder20_3, placeholder21_3, placeholder22_3, placeholder23_3]:
            p.empty()
        st.session_state.Ingreso = False
        st.session_state.Postcampo = False
        st.session_state.Salir = True
        Salir.Salir()

    elif reporte_3:
        marca_3 = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")

        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo:
            st.error("No se encontró un usuario activo para generar el reporte.")
            return

        nombre_3 = usuario_activo["nombre"]
        supervisor_3 = usuario_activo["supervisor"]
        semana_3 = fecha_3.isocalendar()[1]
        año_3 = fecha_3.isocalendar()[0]
        horas_bi = float(horas_3)

        execute(
            """
            INSERT INTO registro (
                marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año, distrito, tipo, lotes, aprobados, rechazados, horas,
                manzana, sector, numero_lote, estado, area, unidades_catastrales, edificas, partida, con_fmi, sin_fmi, observaciones, zona,
                tipo_calidad, horas_bi, area_bi, operador_cc, total_de_errores, errores_por_excepciones, tipo_de_errores, conteo_de_errores
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            params=[
                marca_3, usuario, nombre_3, puesto, supervisor_3, "Descarga Partidas Jurídico",
                fecha_3, semana_3, año_3, distrito_3, tipo_3, 0, 0, 0, horas_3,
                manzana_3, sector_3, numero_lote_3, estado_3, 0.0, unidades_catastrales_3, 0, partida_3,
                0, 0, observaciones_3, "N/A",
                "N/A", horas_bi, 0.0, "N/A", 0, 0, "N/A", 0
            ],
        )
        st.success("Reporte enviado correctamente")
