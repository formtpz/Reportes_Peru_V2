# ----- Librerías ---- #

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute, fetch_operadores_cc, fetch_registros_corregidos_pendientes, actualizar_estado_revision


# ------------------------------------------------------------
# Funciones auxiliares para la carga masiva (Excel)
# (migradas del segundo módulo, sin lógica de personal peruano)
# ------------------------------------------------------------
def formatear_sector_cc(valor):
    try:
        return str(int(float(valor))).zfill(2)
    except:
        return str(valor).zfill(2)


def formatear_manzana_cc(valor):
    try:
        return str(int(float(valor))).zfill(3)
    except:
        return str(valor).zfill(3)


def formatear_lote_cc(valor):
    try:
        valor_str = str(valor).strip()
        if not valor_str or valor_str.lower() == 'nan':
            return 'Todos'
        if valor_str.lower() == 'todos':
            return 'Todos'
        if ',' in valor_str:
            numeros = []
            for num in valor_str.split(','):
                num = num.strip()
                if num:
                    try:
                        numeros.append(str(int(float(num))).zfill(3))
                    except:
                        numeros.append(num)
            return ','.join(numeros) if numeros else 'Todos'
        else:
            return str(int(float(valor_str))).zfill(3)
    except:
        return str(valor)


def normalizar_horas_cc(valor):
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        return float(valor)
    except:
        return 0.0


def normalizar_texto_cc(valor, default="N/A"):
    if pd.isna(valor) or valor == '' or valor is None:
        return default
    return str(valor).strip()


def limpiar_espacios_extra(texto):
    """Elimina espacios dobles y espacios alrededor de comas, y deja un solo espacio entre palabras."""
    if not isinstance(texto, str):
        return texto
    texto = ' '.join(texto.split())
    texto = ', '.join([part.strip() for part in texto.split(',')])
    return texto


def traducir_tipos_errores(valor):
    """Convierte números separados por comas a los nombres de errores según el mapa."""
    mapa = {
        '1': 'Atributos incompletos/erroneos',
        '2': 'Autoensamblado',
        '3': 'Diferencia de áreas',
        '4': 'Errores gráficos',
        '5': 'Puertas no coinciden',
        '6': 'Recapitulación errónea'
    }
    if pd.isna(valor) or valor == '':
        return ''
    texto = str(valor).strip()
    if not texto:
        return ''
    if any(c.isalpha() for c in texto):
        return limpiar_espacios_extra(texto)
    partes = [part.strip() for part in texto.split(',') if part.strip()]
    nombres = []
    for p in partes:
        if p in mapa:
            nombres.append(mapa[p])
        else:
            nombres.append(p)
    return ','.join(nombres)


def buscar_columnas_por_coincidencia_cc(df):
    """Mapea columnas del Excel a los nombres esperados para CC Postcampo."""
    columnas_requeridas = {
        'distrito': ['distrito', 'DISTRITO', 'Distrito', 'Municipio', 'municipio'],
        'sector': ['sector', 'SECTOR', 'Sector', 'sec', 'SEC'],
        'manzana': ['manzana', 'MANZANA', 'Manzana', 'mz', 'MZ'],
        'tipo': ['tipo', 'TIPO', 'Tipo', 'tipo_cc'],
        'operador': ['operador', 'OPERADOR', 'Operador', 'operador_cc', 'Operador CC'],
        'numero_lote': ['numero_lote', 'numero lote', 'NÚMERO LOTE', 'N° Lote', 'lote', 'LOTE', 'n_lote', 'lotes'],
        'tipo_de_errores': ['tipo_de_errores', 'tipo errores', 'TIPO ERRORES', 'Error', 'errores'],
        'aprobados': ['aprobados', 'APROBADOS', 'Aprobados', 'aprob', 'APROB'],
        'rechazados': ['rechazados', 'RECHAZADOS', 'Rechazados', 'rechaz', 'RECHAZ'],
        'horas': ['horas', 'HORAS', 'Horas', 'horas trabajadas', 'horas_trabajadas']
    }
    mapeo = {}
    for nombre_requerido, posibles_nombres in columnas_requeridas.items():
        for posible in posibles_nombres:
            if posible in df.columns:
                mapeo[nombre_requerido] = posible
                break
    return mapeo


def procesar_dataframe_excel_cc(df, opciones_operadores):
    """
    Procesa el DataFrame del Excel, aplica transformaciones y mapea columnas.
    Retorna (df_procesado, columnas_faltantes, mapeo).
    """
    mapeo_columnas = buscar_columnas_por_coincidencia_cc(df)
    columnas_requeridas = [
        'distrito', 'sector', 'manzana', 'tipo', 'operador',
        'numero_lote', 'tipo_de_errores', 'aprobados', 'rechazados', 'horas'
    ]
    columnas_faltantes = [col for col in columnas_requeridas if col not in mapeo_columnas]
    if columnas_faltantes:
        return None, columnas_faltantes, mapeo_columnas

    df_procesado = pd.DataFrame()
    for nombre_requerido, nombre_real in mapeo_columnas.items():
        df_procesado[nombre_requerido] = df[nombre_real]

    df_procesado['sector'] = df_procesado['sector'].apply(formatear_sector_cc)
    df_procesado['manzana'] = df_procesado['manzana'].apply(formatear_manzana_cc)
    df_procesado['numero_lote'] = df_procesado['numero_lote'].apply(
        lambda x: formatear_lote_cc(x) if str(x).strip().lower() != 'todos' else 'Todos'
    )
    df_procesado['horas'] = df_procesado['horas'].apply(normalizar_horas_cc)
    df_procesado['aprobados'] = pd.to_numeric(df_procesado['aprobados'], errors='coerce').fillna(0).astype(int)
    df_procesado['rechazados'] = pd.to_numeric(df_procesado['rechazados'], errors='coerce').fillna(0).astype(int)
    df_procesado['tipo_de_errores'] = df_procesado['tipo_de_errores'].apply(traducir_tipos_errores)
    for col in ['distrito', 'tipo', 'operador', 'numero_lote']:
        df_procesado[col] = df_procesado[col].apply(lambda x: limpiar_espacios_extra(str(x)) if pd.notna(x) else x)

    return df_procesado, [], mapeo_columnas


def validar_datos_masivos_cc(df, distritos_validos, tipos_validos, operadores_validos):
    """Valida el DataFrame procesado antes de insertar."""
    errores = []

    if df is None or df.empty:
        return False, "La tabla está vacía. No hay datos para procesar."

    df_check = df.dropna(how="all")
    if df_check.empty:
        return False, "La tabla está vacía. No hay datos para procesar."

    if df['distrito'].isnull().any() or (df['distrito'] == '').any():
        errores.append("Hay filas sin 'Distrito' seleccionado.")
    else:
        invalidos = df[~df['distrito'].isin(distritos_validos)]
        if not invalidos.empty:
            errores.append(f"Distrito inválido en fila(s): {[i + 1 for i in invalidos.index.tolist()]}")

    if df['tipo'].isnull().any() or (df['tipo'] == '').any():
        errores.append("Hay filas sin 'Tipo' seleccionado.")
    else:
        invalidos = df[~df['tipo'].isin(tipos_validos)]
        if not invalidos.empty:
            errores.append(f"Tipo inválido en fila(s): {[i + 1 for i in invalidos.index.tolist()]}")

    if df['operador'].isnull().any() or (df['operador'] == '').any():
        errores.append("Hay filas sin 'Operador objeto de CC' seleccionado.")
    else:
        invalidos = df[~df['operador'].isin(operadores_validos)]
        if not invalidos.empty:
            errores.append(f"Operador inválido en fila(s): {[i + 1 for i in invalidos.index.tolist()]} (verifica que el nombre coincida exactamente)")

    if (df['horas'] < 0).any():
        errores.append("Hay filas con 'Horas' negativas.")

    if (df['aprobados'] < 0).any():
        errores.append("Hay filas con 'Aprobados' negativos.")

    if (df['rechazados'] < 0).any():
        errores.append("Hay filas con 'Rechazados' negativos.")

    if errores:
        return False, "\n".join(errores)
    return True, "Datos válidos"


def insertar_registros_masivos_cc(df, fecha_seleccionada, usuario, usuario_activo, puesto, estado_reporte):
    """
    Inserta fila por fila en la tabla `registro` para CC Postcampo.
    `estado_reporte` viene del toggle 'Marcar como Corregido por QC' y se aplica
    a todos los registros del lote (igual que en el modo manual).
    """
    marca = datetime.now(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    nombre = usuario_activo["nombre"]
    supervisor = usuario_activo["supervisor"]
    semana = fecha_seleccionada.isocalendar()[1]
    año = fecha_seleccionada.isocalendar()[0]
    registros_insertados = 0

    try:
        for _, row in df.iterrows():
            aprobados = int(row['aprobados'])
            rechazados = int(row['rechazados'])
            unidades_catastrales = aprobados + rechazados
            horas = float(row['horas'])

            tipos_de_errores = normalizar_texto_cc(row.get('tipo_de_errores', ''), default="")
            lista_errores = [t.strip() for t in tipos_de_errores.split(',') if t.strip()]
            tipos_de_errores_str = ','.join(lista_errores)
            conteo_errores = len(lista_errores)

            manzana = formatear_manzana_cc(row['manzana'])
            sector = formatear_sector_cc(row['sector'])
            numero_lote = formatear_lote_cc(row.get('numero_lote', 'Todos'))

            execute(
                """
                INSERT INTO registro (
                  marca,usuario,nombre,puesto,supervisor,proceso,fecha,semana,año,distrito,tipo,lotes,aprobados,rechazados,horas,
                  manzana,sector,numero_lote,estado,area,unidades_catastrales,edificas,partida,con_fmi,sin_fmi,observaciones,zona,
                  tipo_calidad,horas_bi,area_bi,operador_cc,total_de_errores,errores_por_excepciones,tipo_de_errores,conteo_de_errores
                )
                VALUES (
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                  %s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                params=[
                    marca, usuario, nombre, puesto, supervisor, "Control de Calidad Postcampo", fecha_seleccionada, semana, año,
                    row['distrito'], row['tipo'], 0, aprobados, rechazados, horas,
                    manzana, sector, numero_lote, estado_reporte, 0.0, unidades_catastrales, 0, "N/A", 0, 0, "N/A", "N/A",
                    "N/A", horas, 0, row['operador'], 0, 0, tipos_de_errores_str, conteo_errores
                ],
            )
            registros_insertados += 1
        return True, registros_insertados, f"Se insertaron {registros_insertados} registro(s) exitosamente."
    except Exception as e:
        return False, registros_insertados, f"Error al insertar registros: {str(e)}"


# ------------------------------------------------------------
# Función principal del módulo
# ------------------------------------------------------------
def CC_Postcampo(usuario, puesto):

    if "version_tabla_cc" not in st.session_state:
        st.session_state.version_tabla_cc = 0

    # ----- Sidebar (placeholders individuales necesarios para detectar clicks) ----- #
    with st.sidebar:
        ph_sidebar = st.empty()

        with ph_sidebar.container():
            st.title("Menú")
            procesos_3 = st.button("Procesos", key="procesos_3_postcampo")
            historial_3 = st.button("Historial", key="historial_3_postcampo")
            capacitacion_3 = st.button("Capacitaciones", key="capacitacion_3_postcampo")
            otros_registros_3 = st.button("Otros Registros", key="otros_registros_3_postcampo")
            bonos_extras_3 = st.button("Bonos y Extras", key="bonos_extras_3_postcampo")
            salir_3 = st.button("Salir", key="salir_3_postcampo")

    # ----- Contenido Principal (un solo placeholder) ----- #
    ph_main = st.empty()

    # Variables que se definen dentro del container y se usan después, en la navegación
    reporte_3 = False
    subir_masivo = False
    df_editado = None
    fecha_masiva = None

    with ph_main.container():
        st.title(":blue[Control de Calidad Postcampo]")

        # ----- Toggle para marcar como "Corregido por QC" (aplica a manual Y masivo) ----- #
        corregido_qc = st.checkbox(
            "Marcar como Corregido por QC",
            value=False,
            key="corregido_qc_toggle_postcampo",
            help="Active esta opción si el/los reporte(s) ya fueron corregidos por Control de Calidad y NO deben enviarse al operador"
        )

        if corregido_qc:
            st.warning(
                "⚠️ ATENCIÓN: Este/estos reporte(s) no se enviarán al operador para ser corregidos. "
                "Se marcarán como 'Corregido por QC' directamente."
            )

        estado_reporte = "Corregido por QC" if corregido_qc else "N/A"
        # ----- FIN Toggle QC ----- #

        # ----- Selector de modo de carga ----- #
        modo_carga = st.radio(
            "Selecciona el modo de carga:",
            options=["📝 Carga Manual (Formulario)", "📋 Carga Masiva (Subir Excel)"],
            key="modo_cc_postcampo"
        )

        # Listas de valores válidos (usadas en ambos modos)
        distritos_opciones = ("Chorrillos", "San Juan De Miraflores", "Villa el Salvador")
        tipo_opciones = ("Inspección", "Inspección Reproceso", "Primera Reinspección",
                         "Inspección Horas Extras", "Control de Calidad Supervisión")
        tipo_errores_opciones = ("Atributos incompletos/erroneos", "Autoensamblado", "Diferencia de áreas",
                                 "Errores gráficos", "Puertas no coinciden", "Recapitulación errónea")

        operadores_disponibles = fetch_operadores_cc(
            filtro_proceso='Postcampo',
            filtro_subproceso='Productivo',
            filtro_proceso_anterior='Postcampo',
            filtro_subproceso_anterior='Productivo'
        )
        if operadores_disponibles:
            opciones_operadores = [op['nombre'] for op in operadores_disponibles]
        else:
            opciones_operadores = ["No hay operadores disponibles"]

        # ============ MODO MANUAL ============ #
        if modo_carga == "📝 Carga Manual (Formulario)":
            default_date_3 = datetime.now(pytz.timezone('America/Guatemala'))

            fecha_3 = st.date_input("Fecha", value=default_date_3, key="fecha_3_postcampo")

            distrito_3 = st.selectbox("Distrito", options=distritos_opciones, key="municipio_3_postcampo")

            manzana_3 = st.selectbox(
                "Manzana",
                options=tuple(f"{i:03d}" for i in range(1, 121)),
                key="manzana_3_postcampo"
            )

            sector_3 = st.selectbox(
                "Sector",
                options=tuple(f"{i:02d}" for i in range(1, 121)),
                key="sector_3_postcampo"
            )

            lotes = ["Todos"] + [f"{i:03d}" for i in range(1, 249)]
            numero_lote_3 = st.multiselect("Número de Lote", options=lotes, key="numero_lote_3_postcampo")
            if "Todos" in numero_lote_3:
                numero_lote_3 = ["Todos"]
            numero_lote_str = ",".join(numero_lote_3)

            operador_3 = st.selectbox("Operador objeto de CC", options=opciones_operadores, key="operador_3_postcampo")

            tipo_3 = st.selectbox("Tipo", options=tipo_opciones, key="tipo_3_postcampo")

            tipo_de_errores_3 = st.multiselect("Tipo Errores", options=tipo_errores_opciones, key="tipo_de_errores_3_postcampo")

            aprobados_3 = st.number_input("Cantidad de Unidades Catastrales Aprobados", min_value=0, step=1, key="aprobados_3_postcampo")
            rechazados_3 = st.number_input("Cantidad de Unidades Catastrales Rechazados", min_value=0, step=1, key="rechazados_3_postcampo")
            horas_3 = st.number_input("Cantidad de Horas Trabajadas en el Proceso", min_value=0.0, key="horas_3_postcampo")

            reporte_3 = st.button("Generar Reporte", key="reporte_3_postcampo")

        # ============ MODO MASIVO (Excel) ============ #
        else:
            fecha_masiva = st.date_input(
                "📅 Fecha para todos los registros",
                value=datetime.now(pytz.timezone('America/Guatemala')),
                key="fecha_masiva_cc"
            )

            st.info("""
            📋 **Instrucciones:**
            1. Descarga la plantilla Excel oficial (abajo).
            2. Llena tus datos en la **Hoja1** del Excel.
            3. Los nombres de columna pueden variar ligeramente (se detectan por coincidencia).
            4. Sube el archivo Excel.
            5. Revisa la vista previa antes de confirmar.

            **Transformaciones automáticas:**
            - Sector: 1 → 01
            - Manzana: 5 → 005
            - N° Lote: 1 → 001 (o '1,2,3' → '001,002,003')
            - Horas: 8,5 → 8.5
            - Tipo de errores: puedes escribir números separados por comas (ej. 1,3,5) y se traducirán a los nombres correspondientes.
            - Campos vacíos → "N/A" o "Todos".

            ℹ️ El toggle **"Marcar como Corregido por QC"** de arriba aplica a **todos** los registros de este lote.
            """)

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
                st.caption("Descarga el machote oficial `controlcalidadpostcampo.xlsx`")
                st.caption(f"🔗 [Enlace directo]({url_plantilla})")

            archivo_excel = st.file_uploader(
                "📁 Subir archivo Excel con datos",
                type=['xlsx', 'xls'],
                key="archivo_cc_masivo",
                help="Selecciona el archivo Excel con los datos a cargar (Hoja1)"
            )

            if archivo_excel is not None:
                try:
                    df_excel = pd.read_excel(archivo_excel, sheet_name=0)
                    if df_excel.empty:
                        st.error("❌ El archivo Excel está vacío")
                    else:
                        df_procesado, columnas_faltantes, mapeo = procesar_dataframe_excel_cc(df_excel, opciones_operadores)
                        if columnas_faltantes:
                            st.error(f"❌ No se encontraron las siguientes columnas: {', '.join(columnas_faltantes)}")
                            st.info(f"Columnas detectadas en el Excel: {', '.join(df_excel.columns.tolist())}")
                            st.info("💡 Puedes usar nombres similares. Revisa la plantilla oficial para ver los nombres exactos.")
                        else:
                            with st.expander("🔍 Ver mapeo de columnas detectadas"):
                                for nombre_requerido, nombre_real in mapeo.items():
                                    st.write(f"  • '{nombre_real}' → **{nombre_requerido}**")

                            st.subheader("📊 Vista previa de datos procesados")
                            st.caption("✏️ Los datos ya fueron transformados. Puedes editarlos antes de subir.")

                            column_config = {
                                "distrito": st.column_config.SelectboxColumn("Distrito", options=list(distritos_opciones), required=True),
                                "sector": st.column_config.TextColumn("Sector", help="Formateado a 2 dígitos", required=True),
                                "manzana": st.column_config.TextColumn("Manzana", help="Formateado a 3 dígitos", required=True),
                                "tipo": st.column_config.SelectboxColumn("Tipo", options=list(tipo_opciones), required=True),
                                "operador": st.column_config.SelectboxColumn("Operador objeto de CC", options=opciones_operadores, required=True),
                                "numero_lote": st.column_config.TextColumn("N° Lote", help="Ej: 1,2,3 o 'Todos'"),
                                "tipo_de_errores": st.column_config.TextColumn("Tipo Errores", help="Puedes ingresar números (1,3,5) o nombres separados por coma"),
                                "aprobados": st.column_config.NumberColumn("Aprobados", min_value=0, step=1, required=True),
                                "rechazados": st.column_config.NumberColumn("Rechazados", min_value=0, step=1, required=True),
                                "horas": st.column_config.NumberColumn("Horas", min_value=0.0, format="%.2f", required=True)
                            }

                            df_editado = st.data_editor(
                                df_procesado,
                                num_rows="dynamic",
                                use_container_width=True,
                                hide_index=True,
                                column_config=column_config,
                                key=f"editor_masivo_cc_{st.session_state.version_tabla_cc}"
                            )

                            if df_editado is not None and not df_editado.empty:
                                df_editado['sector'] = df_editado['sector'].apply(formatear_sector_cc)
                                df_editado['manzana'] = df_editado['manzana'].apply(formatear_manzana_cc)
                                df_editado['numero_lote'] = df_editado['numero_lote'].apply(
                                    lambda x: formatear_lote_cc(x) if str(x).strip().lower() != 'todos' else 'Todos'
                                )
                                df_editado['horas'] = df_editado['horas'].apply(normalizar_horas_cc)
                                df_editado['aprobados'] = pd.to_numeric(df_editado['aprobados'], errors='coerce').fillna(0).astype(int)
                                df_editado['rechazados'] = pd.to_numeric(df_editado['rechazados'], errors='coerce').fillna(0).astype(int)
                                df_editado['tipo_de_errores'] = df_editado['tipo_de_errores'].apply(traducir_tipos_errores)
                                for col in ['distrito', 'tipo', 'operador', 'numero_lote']:
                                    df_editado[col] = df_editado[col].apply(lambda x: limpiar_espacios_extra(str(x)) if pd.notna(x) else x)

                            if df_editado is not None and not df_editado.empty:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("📊 Registros", len(df_editado))
                                with col2:
                                    st.metric("🏘️ Sectores", df_editado['sector'].nunique())
                                with col3:
                                    st.metric("🏠 Manzanas", df_editado['manzana'].nunique())

                except Exception as e:
                    st.error(f"❌ Error al leer el archivo Excel: {str(e)}")
                    st.info("💡 Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls) y que los datos estén en la Hoja1")

            subir_masivo = st.button(
                "🚀 Subir Registros Masivos",
                type="primary",
                use_container_width=True,
                key="subir_masivo_cc",
                disabled=(df_editado is None or df_editado.empty)
            )

        # ============ TABLA DE REGISTROS PENDIENTES (SIEMPRE VISIBLE, EN AMBOS MODOS) ============ #
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
                key="tabla_revision_postcampo"
            )

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("💾 Guardar cambios de estado", key="guardar_revision_postcampo", use_container_width=True):
                    registros_a_actualizar = edited_df[edited_df['marcar_revisado'] == True]

                    if len(registros_a_actualizar) > 0:
                        actualizaciones_exitosas = 0
                        actualizaciones_fallidas = 0

                        for _, row in registros_a_actualizar.iterrows():
                            if actualizar_estado_revision(row['id']):
                                actualizaciones_exitosas += 1
                            else:
                                actualizaciones_fallidas += 1

                        if actualizaciones_fallidas == 0:
                            st.success(f'✅ {actualizaciones_exitosas} registro(s) actualizado(s) a "revisado" exitosamente')
                        else:
                            st.warning(f'⚠️ {actualizaciones_exitosas} exitoso(s), {actualizaciones_fallidas} fallido(s)')

                        st.rerun()
                    else:
                        st.warning("⚠️ No se seleccionó ningún registro para actualizar.")
        else:
            st.info("ℹ️ No hay registros pendientes de revisión con estado 'corregido' en este momento.")

        # ============ FIN TABLA ============ #

    # ----- Navegación (SOLO se limpian ph_main y ph_sidebar) ----- #

    if procesos_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Procesos = True

        usuario_activo = obtener_usuario_activo(usuario)
        perfil = str(usuario_activo["perfil"]) if usuario_activo else ""

        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)

    elif historial_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_registros_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_extras_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_3:
        ph_main.empty()
        ph_sidebar.empty()
        st.session_state.CC_Postcampo = False
        st.session_state.Ingreso = False
        st.session_state.Salir = True
        Salir.Salir()

    # ----- Generar Reporte (modo manual) ----- #
    elif reporte_3:
        marca_3 = datetime.now(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")

        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo:
            st.error("No se encontró un usuario activo para generar el reporte.")
            return

        nombre_3 = usuario_activo["nombre"]
        supervisor_3 = usuario_activo["supervisor"]

        unidades_catastrales_3 = aprobados_3 + rechazados_3
        semana_3 = fecha_3.isocalendar()[1]
        año_3 = fecha_3.isocalendar()[0]
        horas_bi = float(horas_3)
        tipos_de_errores_str = ','.join(tipo_de_errores_3)
        conteo_3 = len(tipo_de_errores_3)

        execute(
            """
            INSERT INTO registro (
                marca,usuario,nombre,puesto,supervisor,proceso,fecha,semana,año,distrito,tipo,lotes,aprobados,rechazados,horas,
                manzana,sector,numero_lote,estado,area,unidades_catastrales,edificas,partida,con_fmi,sin_fmi,observaciones,zona,
                tipo_calidad,horas_bi,area_bi,operador_cc,total_de_errores,errores_por_excepciones,tipo_de_errores,conteo_de_errores
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s
            )
            """,
            params=[
                marca_3, usuario, nombre_3, puesto, supervisor_3, "Control de Calidad Postcampo",
                fecha_3, semana_3, año_3, distrito_3, tipo_3, 0, aprobados_3, rechazados_3, horas_3,
                manzana_3, sector_3, numero_lote_str, estado_reporte, 0.0, unidades_catastrales_3,
                0, "N/A", 0, 0, "N/A", "N/A",
                "N/A", horas_bi, 0, operador_3, 0, 0, tipos_de_errores_str, conteo_3
            ],
        )
        st.success('✅ Reporte enviado correctamente')

    # ----- Subir Registros Masivos (modo Excel) ----- #
    elif subir_masivo and df_editado is not None:
        with st.spinner("⏳ Validando datos..."):
            es_valido, mensaje_validacion = validar_datos_masivos_cc(
                df_editado, list(distritos_opciones), list(tipo_opciones), opciones_operadores
            )
            if not es_valido:
                st.error(f"❌ Error de validación:\n{mensaje_validacion}")
                st.warning("⚠️ No se subió ningún registro. Corrige los errores e intenta de nuevo.")
            else:
                st.success("✅ Validación exitosa")
                usuario_activo = obtener_usuario_activo(usuario)
                if not usuario_activo:
                    st.error("No se encontró un usuario activo para generar el reporte.")
                    return
                with st.spinner("💾 Insertando registros en la base de datos..."):
                    exito, insertados, mensaje = insertar_registros_masivos_cc(
                        df_editado, fecha_masiva, usuario, usuario_activo, puesto, estado_reporte
                    )
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.balloons()
                        st.session_state.version_tabla_cc += 1
                    else:
                        st.error(f"❌ {mensaje}")
                        st.error(f"Se insertaron {insertados} registro(s) antes del error.")
