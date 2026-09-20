# ----- Librerías ---- #
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import (
    insertar_registro_con_detalle_qa,
    fetch_registros_corregidos_pendientes,
    actualizar_estado_revision,
)


# ------------------------------------------------------------
# Constantes
# ------------------------------------------------------------
DISTRITOS_OPCIONES = ("Chorrillos", "San Juan De Miraflores", "Villa el Salvador")
TIPO_OPCIONES = ("Inspección", "Inspección Horas Extras")
NOMBRE_PROCESO_BD = "Control de Calidad QA1"

COLUMNAS_EXCEL_QA = {
    'crc':        ['crc', 'CRC', 'Crc', 'código', 'codigo', 'CODIGO', 'Codigo'],
    'aprobados':  ['aprobados', 'APROBADOS', 'Aprobados', 'aprobado', 'APROBADO', 'Aprobado'],
    'rechazados': ['rechazados', 'RECHAZADOS', 'Rechazados', 'rechazado', 'RECHAZADO', 'Rechazado'],
}


# ------------------------------------------------------------
# Funciones auxiliares para el Excel
# ------------------------------------------------------------
def buscar_columnas_excel_qa(df):
    """Devuelve un dict {nombre_requerido: nombre_real_en_excel}."""
    mapeo = {}
    for nombre_requerido, posibles in COLUMNAS_EXCEL_QA.items():
        for posible in posibles:
            if posible in df.columns:
                mapeo[nombre_requerido] = posible
                break
    return mapeo


def procesar_excel_qa(df):
    """
    Procesa el Excel de QA (crc, aprobados, rechazados).
    Retorna (df_procesado, columnas_faltantes, mapeo).
    """
    mapeo = buscar_columnas_excel_qa(df)
    requeridas = ['crc', 'aprobados', 'rechazados']
    faltantes = [c for c in requeridas if c not in mapeo]
    if faltantes:
        return None, faltantes, mapeo

    df_proc = pd.DataFrame()
    for nombre_req, nombre_real in mapeo.items():
        df_proc[nombre_req] = df[nombre_real]

    # Normalizar
    df_proc['crc'] = df_proc['crc'].fillna('').astype(str).str.strip()
    df_proc['aprobados'] = pd.to_numeric(df_proc['aprobados'], errors='coerce').fillna(0).astype(int)
    df_proc['rechazados'] = pd.to_numeric(df_proc['rechazados'], errors='coerce').fillna(0).astype(int)

    # Quitar filas sin CRC
    df_proc = df_proc[df_proc['crc'] != ''].reset_index(drop=True)

    return df_proc, [], mapeo


def validar_excel_qa(df):
    """Valida el DataFrame procesado antes de insertar."""
    if df is None or df.empty:
        return False, "El Excel no tiene datos válidos."

    errores = []
    if (df['aprobados'] < 0).any():
        errores.append("Hay filas con 'aprobados' negativos.")
    if (df['rechazados'] < 0).any():
        errores.append("Hay filas con 'rechazados' negativos.")
    if df['crc'].duplicated().any():
        errores.append("Hay CRC duplicados en el Excel. Revisa el archivo.")

    if errores:
        return False, "\n".join(errores)
    return True, "Datos válidos"


# ------------------------------------------------------------
# Inserción atómica: registro global + detalle QA1
# ------------------------------------------------------------
def insertar_qa_completo(usuario, puesto, usuario_activo, fecha_sel,
                         distrito, tipo, horas, df_detalle):
    """Inserta el registro padre y sus detalles QA1 de una sola vez."""
    marca = datetime.now(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    nombre = usuario_activo["nombre"]
    supervisor = usuario_activo["supervisor"]
    semana = fecha_sel.isocalendar()[1]
    año = fecha_sel.isocalendar()[0]

    total_aprobados = int(df_detalle['aprobados'].sum())
    total_rechazados = int(df_detalle['rechazados'].sum())
    unidades_catastrales = total_aprobados + total_rechazados

    datos_registro = {
        'marca': marca,
        'usuario': usuario,
        'nombre': nombre,
        'puesto': puesto,
        'supervisor': supervisor,
        'proceso': NOMBRE_PROCESO_BD,
        'fecha': fecha_sel,
        'semana': semana,
        'año': año,
        'distrito': distrito,
        'tipo': tipo,
        'lotes': 0,
        'aprobados': total_aprobados,
        'rechazados': total_rechazados,
        'horas': float(horas),
        'manzana': '0',
        'sector': '0',
        'numero_lote': '0',
        'estado': 'N/A',
        'area': 0.0,
        'unidades_catastrales': unidades_catastrales,
        'edificas': 0,
        'partida': 'N/A',
        'con_fmi': 0,
        'sin_fmi': 0,
        'observaciones': 'N/A',
        'zona': 'N/A',
        'tipo_calidad': 'N/A',
        'horas_bi': float(horas),
        'area_bi': 0,
        'operador_cc': 'N/A',
        'total_de_errores': 0,
        'errores_por_excepciones': 0,
        'tipo_de_errores': 'N/A',
        'conteo_de_errores': 0,
    }

    detalles_qa = [
        (str(row['crc']).strip(), int(row['aprobados']), int(row['rechazados']))
        for _, row in df_detalle.iterrows()
    ]

    try:
        id_registro = insertar_registro_con_detalle_qa(datos_registro, detalles_qa)
        return True, f"Registro #{id_registro} creado con {len(detalles_qa)} CRC(s)."
    except Exception as e:
        return False, f"Error al insertar: {str(e)}"


# ------------------------------------------------------------
# Función principal del módulo
# ------------------------------------------------------------
def CC_Postcampo(usuario, puesto):

    if "version_tabla_qa1" not in st.session_state:
        st.session_state.version_tabla_qa1 = 0

    # ----- Sidebar ----- #
    with st.sidebar:
        ph_sidebar = st.empty()
        with ph_sidebar.container():
            st.title("Menú")
            procesos_3 = st.button("Procesos", key="procesos_3_qa1")
            historial_3 = st.button("Historial", key="historial_3_qa1")
            capacitacion_3 = st.button("Capacitaciones", key="capacitacion_3_qa1")
            otros_registros_3 = st.button("Otros Registros", key="otros_registros_3_qa1")
            bonos_extras_3 = st.button("Bonos y Extras", key="bonos_extras_3_qa1")
            salir_3 = st.button("Salir", key="salir_3_qa1")

    # ----- Contenido principal ----- #
    ph_main = st.empty()

    reporte_btn = False
    df_detalle = None

    with ph_main.container():
        st.title(":blue[Control de Calidad QA1]")

        # ----- Formulario ----- #
        default_date = datetime.now(pytz.timezone('America/Guatemala'))
        fecha_sel = st.date_input("Fecha", value=default_date, key="fecha_qa1")
        distrito_sel = st.selectbox("Distrito", options=DISTRITOS_OPCIONES, key="distrito_qa1")
        tipo_sel = st.selectbox("Tipo", options=TIPO_OPCIONES, key="tipo_qa1")
        horas_sel = st.number_input(
            "Cantidad de Horas Trabajadas en el Proceso",
            min_value=0.0, step=0.5,
            key="horas_qa1"
        )

        # ----- Excel ----- #
        st.markdown("### 📥 Plantilla oficial")
        url_plantilla = "https://raw.githubusercontent.com/formtpz/Reportes_Peru_V2/main/docs/controlcalidadpostcampo.xlsx"
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f'''
            <a href="{url_plantilla}" download>
                <button style="background-color: #4CAF50; color: white; padding: 10px 20px;
                border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                    📥 Descargar Plantilla
                </button>
            </a>
            ''', unsafe_allow_html=True)
        with col2:
            st.caption("Columnas esperadas: **crc**, **aprobados**, **rechazados**")
            st.caption(f"🔗 [Enlace directo]({url_plantilla})")

        archivo_excel = st.file_uploader(
            "📁 Subir archivo Excel con los CRC",
            type=['xlsx', 'xls'],
            key="archivo_qa1",
            help="Selecciona el Excel con las columnas crc, aprobados, rechazados"
        )

        if archivo_excel is not None:
            try:
                df_excel = pd.read_excel(archivo_excel, sheet_name=0)
                if df_excel.empty:
                    st.error("❌ El archivo Excel está vacío.")
                else:
                    df_procesado, faltantes, mapeo = procesar_excel_qa(df_excel)
                    if faltantes:
                        st.error(f"❌ No se encontraron las columnas: {', '.join(faltantes)}")
                        st.info(f"Columnas detectadas: {', '.join(df_excel.columns.tolist())}")
                    else:
                        with st.expander("🔍 Ver mapeo de columnas detectadas"):
                            for nombre_req, nombre_real in mapeo.items():
                                st.write(f"  • '{nombre_real}' → **{nombre_req}**")

                        st.subheader("📊 Vista previa de datos")
                        st.caption("✏️ Puedes editar los valores antes de subir.")

                        df_detalle = st.data_editor(
                            df_procesado,
                            num_rows="dynamic",
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "crc": st.column_config.TextColumn("CRC", required=True),
                                "aprobados": st.column_config.NumberColumn("Aprobados", min_value=0, step=1, required=True),
                                "rechazados": st.column_config.NumberColumn("Rechazados", min_value=0, step=1, required=True),
                            },
                            key=f"editor_qa1_{st.session_state.version_tabla_qa1}"
                        )

                        if df_detalle is not None and not df_detalle.empty:
                            # Reforzar tipos
                            df_detalle['crc'] = df_detalle['crc'].fillna('').astype(str).str.strip()
                            df_detalle['aprobados'] = pd.to_numeric(df_detalle['aprobados'], errors='coerce').fillna(0).astype(int)
                            df_detalle['rechazados'] = pd.to_numeric(df_detalle['rechazados'], errors='coerce').fillna(0).astype(int)
                            # Quitar filas sin CRC
                            df_detalle = df_detalle[df_detalle['crc'] != ''].reset_index(drop=True)

                            # Métricas
                            total_ap = int(df_detalle['aprobados'].sum())
                            total_re = int(df_detalle['rechazados'].sum())
                            c1, c2, c3, c4 = st.columns(4)
                            c1.metric("📊 Filas", len(df_detalle))
                            c2.metric("✅ Aprobados", total_ap)
                            c3.metric("❌ Rechazados", total_re)
                            c4.metric("📦 Total UC", total_ap + total_re)

                            # Aviso si hay filas con suma != 1
                            raras = df_detalle[(df_detalle['aprobados'] + df_detalle['rechazados']) != 1]
                            if not raras.empty:
                                st.warning(
                                    f"⚠️ Hay {len(raras)} fila(s) donde aprobados + rechazados ≠ 1. "
                                    "Verifica el Excel (lo normal es que cada CRC sea 1 en aprobado o 1 en rechazado)."
                                )

            except Exception as e:
                st.error(f"❌ Error al leer el Excel: {e}")

        # ----- Botón generar reporte ----- #
        reporte_btn = st.button(
            "🚀 Generar Reporte",
            type="primary",
            use_container_width=True,
            key="reporte_qa1",
            disabled=(df_detalle is None or df_detalle.empty or horas_sel <= 0)
        )

        if horas_sel <= 0:
            st.info("ℹ️ Ingresa una cantidad de horas mayor a 0 para habilitar el botón.")

        # ----- Tabla de registros pendientes de revisión ----- #
        st.markdown("---")
        st.subheader("📋 Registros pendientes de revisión")
        df_pendientes = fetch_registros_corregidos_pendientes(usuario)

        if not df_pendientes.empty:
            df_pendientes['marcar_revisado'] = False
            st.info(f"Se encontraron {len(df_pendientes)} registro(s) pendiente(s) de revisión")

            edited_df = st.data_editor(
                df_pendientes,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "marca": st.column_config.DatetimeColumn("Fecha Registro", disabled=True),
                    "fecha": st.column_config.DateColumn("Fecha", disabled=True),
                    "distrito": st.column_config.TextColumn("Distrito", disabled=True),
                    "manzana": st.column_config.TextColumn("Manzana", disabled=True),
                    "sector": st.column_config.TextColumn("Sector", disabled=True),
                    "numero_lote": st.column_config.TextColumn("Lotes", disabled=True),
                    "operador_cc": st.column_config.TextColumn("Operador CC", disabled=True),
                    "tipo_de_errores": st.column_config.TextColumn("Tipo de Errores", disabled=True),
                    "estado": st.column_config.TextColumn("Estado Actual", disabled=True),
                    "marcar_revisado": st.column_config.CheckboxColumn(
                        "Marcar como Revisado",
                        help="Seleccione para cambiar el estado a 'revisado'"
                    )
                },
                hide_index=True,
                key="tabla_revision_qa1"
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Guardar cambios de estado", key="guardar_revision_qa1", use_container_width=True):
                    a_actualizar = edited_df[edited_df['marcar_revisado'] == True]
                    if len(a_actualizar) > 0:
                        exitos = 0
                        fallos = 0
                        for _, row in a_actualizar.iterrows():
                            if actualizar_estado_revision(row['id']):
                                exitos += 1
                            else:
                                fallos += 1
                        if fallos == 0:
                            st.success(f'✅ {exitos} registro(s) actualizado(s) a "revisado".')
                        else:
                            st.warning(f'⚠️ {exitos} exitoso(s), {fallos} fallido(s).')
                        st.rerun()
                    else:
                        st.warning("⚠️ No se seleccionó ningún registro.")
        else:
            st.info("ℹ️ No hay registros pendientes de revisión.")

    # ============================================================
    # Navegación
    # ============================================================
    if procesos_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Procesos = True
        ua = obtener_usuario_activo(usuario)
        perfil = str(ua["perfil"]) if ua else ""
        if perfil == "1": Procesos.Procesos1(usuario, puesto)
        elif perfil == "2": Procesos.Procesos2(usuario, puesto)
        elif perfil == "3": Procesos.Procesos3(usuario, puesto)

    elif historial_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_registros_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_extras_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_3:
        ph_main.empty(); ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Ingreso = False
        st.session_state.Salir = True
        Salir.Salir()

    # ============================================================
    # Generar reporte
    # ============================================================
    elif reporte_btn and df_detalle is not None and not df_detalle.empty:
        # Validación final
        es_valido, msg = validar_excel_qa(df_detalle)
        if not es_valido:
            st.error(f"❌ Error de validación:\n{msg}")
        else:
            usuario_activo = obtener_usuario_activo(usuario)
            if not usuario_activo:
                st.error("No se encontró un usuario activo para generar el reporte.")
                return

            with st.spinner("💾 Insertando registro y detalle QA1..."):
                exito, mensaje = insertar_qa_completo(
                    usuario, puesto, usuario_activo,
                    fecha_sel, distrito_sel, tipo_sel,
                    horas_sel, df_detalle
                )

            if exito:
                st.success(f"✅ {mensaje}")
                st.balloons()
                st.session_state.version_tabla_qa1 += 1
            else:
                st.error(f"❌ {mensaje}")
