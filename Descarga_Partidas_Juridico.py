# ----- Librerías ---- #
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io
import Procesos, Historial, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute

# ------------------------------------------------------------
# Funciones auxiliares para la carga masiva (idénticas a Precampo_Juridico)
# ------------------------------------------------------------
def formatear_sector(valor):
    try:
        return str(int(float(valor))).zfill(2)
    except:
        return str(valor).zfill(2)

def formatear_manzana(valor):
    try:
        return str(int(float(valor))).zfill(3)
    except:
        return str(valor).zfill(3)

def formatear_lote(valor):
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
            return ', '.join(numeros) if numeros else 'Todos'
        else:
            return str(int(float(valor_str))).zfill(3)
    except:
        return str(valor)

def normalizar_horas(valor):
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        return float(valor)
    except:
        return 0.0

def normalizar_texto(valor, default="N/A"):
    if pd.isna(valor) or valor == '' or valor is None:
        return default
    return str(valor)

def buscar_columnas_por_coincidencia(df):
    columnas_requeridas = {
        'distrito': ['distrito', 'DISTRITO', 'Distrito'],
        'sector': ['sector', 'SECTOR', 'Sector'],
        'manzana': ['manzana', 'MANZANA', 'Manzana', 'mz', 'MZ'],
        'tipo': ['tipo', 'TIPO', 'Tipo'],
        'estado': ['estado', 'ESTADO', 'Estado'],
        'numero_lote': ['numero_lote', 'numero lote', 'NÚMERO LOTE', 'N° Lote', 'lote', 'LOTE', 'n_lote'],
        'partida': ['partida', 'PARTIDA', 'Partida', 'n° partida', 'n_partida'],
        'unidades_catastrales': ['unidades_catastrales', 'unidades catastrales', 'UNIDADES CATASTRALES',
                                 'cantidad_registros', 'cantidad registros', 'registros', 'cant_registros'],
        'horas': ['horas', 'HORAS', 'Horas', 'horas trabajadas', 'horas_trabajadas'],
        'observaciones': ['observaciones', 'OBSERVACIONES', 'Observaciones', 'obs', 'OBS']
    }
    mapeo = {}
    for nombre_requerido, posibles_nombres in columnas_requeridas.items():
        for posible in posibles_nombres:
            if posible in df.columns:
                mapeo[nombre_requerido] = posible
                break
    return mapeo

def procesar_dataframe_excel(df):
    mapeo_columnas = buscar_columnas_por_coincidencia(df)
    columnas_requeridas = [
        'distrito', 'sector', 'manzana', 'tipo', 'estado',
        'numero_lote', 'partida', 'unidades_catastrales', 'horas', 'observaciones'
    ]
    columnas_faltantes = [col for col in columnas_requeridas if col not in mapeo_columnas]
    if columnas_faltantes:
        return None, columnas_faltantes, mapeo_columnas

    df_procesado = pd.DataFrame()
    for nombre_requerido, nombre_real in mapeo_columnas.items():
        df_procesado[nombre_requerido] = df[nombre_real]

    df_procesado['sector'] = df_procesado['sector'].apply(formatear_sector)
    df_procesado['manzana'] = df_procesado['manzana'].apply(formatear_manzana)
    df_procesado['numero_lote'] = df_procesado['numero_lote'].apply(
        lambda x: formatear_lote(x) if str(x).strip().lower() != 'todos' else 'Todos'
    )
    df_procesado['horas'] = df_procesado['horas'].apply(normalizar_horas)
    df_procesado['unidades_catastrales'] = pd.to_numeric(
        df_procesado['unidades_catastrales'].apply(
            lambda x: str(x).replace(',', '.') if isinstance(x, str) else x
        ), errors='coerce'
    ).fillna(0).astype(int)
    df_procesado['observaciones'] = df_procesado['observaciones'].apply(lambda x: normalizar_texto(x, "N/A"))
    df_procesado['partida'] = df_procesado['partida'].apply(lambda x: normalizar_texto(x, "N/A"))
    df_procesado['numero_lote'] = df_procesado['numero_lote'].apply(lambda x: normalizar_texto(x, "Todos"))
    return df_procesado, [], mapeo_columnas

def validar_datos_masivos(df, fecha_seleccionada):
    errores = []
    if df.empty:
        return False, "La tabla está vacía. No hay datos para procesar."
    columnas_requeridas = ['distrito', 'sector', 'manzana', 'tipo', 'estado']
    for col in columnas_requeridas:
        nulos = df[col].isnull().sum()
        if nulos > 0:
            errores.append(f"La columna '{col}' tiene {nulos} valores nulos")
    distritos_validos = ["Chorrillos", "San Juan De Miraflores", "Villa el Salvador"]
    distritos_invalidos = df[~df['distrito'].isin(distritos_validos)]
    if not distritos_invalidos.empty:
        errores.append(f"Hay {len(distritos_invalidos)} registros con distrito inválido en filas: {distritos_invalidos.index.tolist()}")
    tipos_validos = ["Ordinario", "Reproceso Ordinario", "Corrección de Calidad",
                     "Corrección de Calidad Extraordinaria", "Producción Horas Extras"]
    tipos_invalidos = df[~df['tipo'].isin(tipos_validos)]
    if not tipos_invalidos.empty:
        errores.append(f"Hay {len(tipos_invalidos)} registros con tipo inválido en filas: {tipos_invalidos.index.tolist()}")
    estados_validos = ["Finalizado", "En Conflicto"]
    estados_invalidos = df[~df['estado'].isin(estados_validos)]
    if not estados_invalidos.empty:
        errores.append(f"Hay {len(estados_invalidos)} registros con estado inválido en filas: {estados_invalidos.index.tolist()}")
    horas_invalidas = df[df['horas'] < 0]
    if not horas_invalidas.empty:
        errores.append(f"Hay {len(horas_invalidas)} registros con horas negativas")
    uc_invalidas = df[df['unidades_catastrales'] < 0]
    if not uc_invalidas.empty:
        errores.append(f"Hay {len(uc_invalidas)} registros con unidades catastrales negativas")
    if errores:
        return False, "\n".join(errores)
    return True, "Datos válidos"

def insertar_registros_masivos(df, fecha_seleccionada, usuario, usuario_activo):
    try:
        marca = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
        nombre = usuario_activo["nombre"]
        supervisor = usuario_activo["supervisor"]
        puesto = usuario_activo.get("puesto", "")
        semana = fecha_seleccionada.isocalendar()[1]
        año = fecha_seleccionada.isocalendar()[0]
        registros_insertados = 0

        for index, row in df.iterrows():
            sector_formateado = row['sector']
            manzana_formateada = row['manzana']
            horas = float(row['horas'])
            horas_bi = horas
            unidades_catastrales = int(row['unidades_catastrales'])
            partida = str(row['partida'])
            observaciones = str(row['observaciones'])
            numero_lote = str(row['numero_lote'])

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
                    marca, usuario, nombre, puesto, supervisor, "Descarga Partidas Jurídico",
                    fecha_seleccionada, semana, año, row['distrito'], row['tipo'], 0, 0, 0, horas,
                    manzana_formateada, sector_formateado, numero_lote, row['estado'],
                    0.0, unidades_catastrales, 0, partida, 0, 0, observaciones, "N/A",
                    "N/A", horas_bi, 0.0, "N/A", 0, 0, "N/A", 0
                ],
            )
            registros_insertados += 1
        return True, registros_insertados, f"Se insertaron {registros_insertados} registros exitosamente"
    except Exception as e:
        return False, registros_insertados, f"Error al insertar registros: {str(e)}"

# ------------------------------------------------------------
# Función principal del módulo
# ------------------------------------------------------------
def Descarga_Partidas_Juridico(usuario, puesto):

    # ----- Placeholders del sidebar -----
    placeholder1 = st.sidebar.empty()
    placeholder1.title("Menú")
    placeholder2 = st.sidebar.empty()
    procesos_btn = placeholder2.button("Procesos", key="procesos_descarga")
    placeholder3 = st.sidebar.empty()
    historial_btn = placeholder3.button("Historial", key="historial_descarga")
    placeholder4 = st.sidebar.empty()
    capacitacion_btn = placeholder4.button("Capacitaciones", key="capacitacion_descarga")
    placeholder5 = st.sidebar.empty()
    otros_btn = placeholder5.button("Otros Registros", key="otros_descarga")
    placeholder6 = st.sidebar.empty()
    bonos_btn = placeholder6.button("Bonos y Horas Extras", key="bonos_descarga")
    placeholder7 = st.sidebar.empty()
    salir_btn = placeholder7.button("Salir", key="salir_descarga")

    # ----- Selector de modo de carga -----
    placeholder_modo = st.empty()
    modo_carga = placeholder_modo.radio(
        "Selecciona el modo de carga:",
        options=["📝 Carga Manual (Formulario)", "📋 Carga Masiva (Subir Excel)"],
        key="modo_descarga_partidas"
    )

    # ----- Título -----
    placeholder_titulo = st.empty()
    placeholder_titulo.title("Descarga Partidas Jurídico")

    # Inicialización de placeholders del formulario manual
    placeholder_fecha = None
    placeholder_distrito = None
    placeholder_sector = None
    placeholder_manzana = None
    placeholder_tipo = None
    placeholder_estado = None
    placeholder_lote = None
    placeholder_partida = None
    placeholder_uc = None
    placeholder_horas = None
    placeholder_obs = None
    placeholder_reporte = None

    # Variables del formulario manual
    fecha = None
    distrito = None
    sector = None
    manzana = None
    tipo = None
    estado = None
    numero_lote = None
    partida = None
    unidades_catastrales = None
    horas = None
    observaciones = None
    reporte_btn = None

    # ----- Modo manual -----
    if modo_carga == "📝 Carga Manual (Formulario)":
        default_date = datetime.now(pytz.timezone('America/Guatemala'))

        placeholder_fecha = st.empty()
        fecha = placeholder_fecha.date_input("Fecha", value=default_date, key="fecha_descarga")

        placeholder_distrito = st.empty()
        distrito = placeholder_distrito.selectbox(
            "Distrito",
            options=("Chorrillos", "San Juan De Miraflores", "Villa el Salvador"),
            key="distrito_descarga"
        )

        placeholder_sector = st.empty()
        sector = placeholder_sector.selectbox(
            "Sector",
            options=[f"{i:02d}" for i in range(1, 121)],
            key="sector_descarga"
        )

        placeholder_manzana = st.empty()
        manzana = placeholder_manzana.selectbox(
            "Manzana",
            options=[f"{i:03d}" for i in range(1, 121)],
            key="manzana_descarga"
        )

        placeholder_tipo = st.empty()
        tipo = placeholder_tipo.selectbox(
            "Tipo",
            options=("Ordinario", "Reproceso Ordinario", "Corrección de Calidad",
                     "Corrección de Calidad Extraordinaria", "Producción Horas Extras"),
            key="tipo_descarga"
        )

        placeholder_estado = st.empty()
        estado = placeholder_estado.selectbox(
            "Estado",
            options=("Finalizado", "En Conflicto"),
            key="estado_descarga"
        )

        # Multiselect de lotes
        lotes = ["Todos"] + [f"{i:03d}" for i in range(1, 249)]
        placeholder_lote = st.empty()
        numero_lote_seleccion = placeholder_lote.multiselect(
            "Número de Lote",
            options=lotes,
            key="lote_descarga"
        )
        if "Todos" in numero_lote_seleccion:
            numero_lote_seleccion = ["Todos"]
        numero_lote = ",".join(numero_lote_seleccion)

        placeholder_partida = st.empty()
        partida = placeholder_partida.text_input("Número de Partida", value="N/A", max_chars=60, key="partida_descarga")

        placeholder_uc = st.empty()
        unidades_catastrales = placeholder_uc.number_input(
            "Cantidad de Registros",
            min_value=0,
            step=1,
            key="uc_descarga"
        )

        placeholder_horas = st.empty()
        horas = placeholder_horas.number_input(
            "Cantidad de Horas Trabajadas en el Proceso",
            min_value=0.0,
            key="horas_descarga"
        )

        placeholder_obs = st.empty()
        observaciones = placeholder_obs.text_input("Observaciones", value="N/A", max_chars=60, key="obs_descarga")

        placeholder_reporte = st.empty()
        reporte_btn = placeholder_reporte.button("Generar Reporte", key="reporte_descarga")

    # ----- Modo masivo -----
    else:
        placeholder_fecha_masiva = st.empty()
        fecha_masiva = placeholder_fecha_masiva.date_input(
            "📅 Fecha para todos los registros",
            value=datetime.now(pytz.timezone('America/Guatemala')),
            key="fecha_masiva_descarga"
        )

        placeholder_instrucciones = st.empty()
        with placeholder_instrucciones.container():
            st.info("""
            📋 **Instrucciones:**
            1. Descarga la plantilla Excel oficial (abajo)
            2. Llena tus datos en la **Hoja1** del Excel
            3. Los nombres de columna pueden variar ligeramente (se detectan por coincidencia)
            4. Sube el archivo Excel
            5. Revisa la vista previa antes de confirmar

            **Transformaciones automáticas:**
            - Sector: 1 → 01
            - Manzana: 5 → 005
            - N° Lote: 1 → 001
            - Horas: 8,5 → 8.5
            - Campos vacíos → "N/A" o "Todos"
            """)

        placeholder_descarga_plantilla = st.empty()
        with placeholder_descarga_plantilla.container():
            st.markdown("### 📥 Plantilla oficial")
            # Cambia la URL por la plantilla real de Descarga Partidas Jurídico
            url_plantilla = "https://raw.githubusercontent.com/formtpz/Reportes_Peru_V2/main/docs/descargapartidasjuridico.xlsx"
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
                st.caption("Descarga el machote oficial `descargapartidasjuridico.xlsx`")
                st.caption(f"🔗 [Enlace directo]({url_plantilla})")

        placeholder_archivo = st.empty()
        archivo_excel = placeholder_archivo.file_uploader(
            "📁 Subir archivo Excel con datos",
            type=['xlsx', 'xls'],
            key="archivo_descarga_masivo",
            help="Selecciona el archivo Excel con los datos a cargar (Hoja1)"
        )

        df_editado = None
        placeholder_tabla = st.empty()
        placeholder_estadisticas = st.empty()

        if archivo_excel is not None:
            try:
                df_excel = pd.read_excel(archivo_excel, sheet_name=0)
                if df_excel.empty:
                    with placeholder_tabla.container():
                        st.error("❌ El archivo Excel está vacío")
                else:
                    df_procesado, columnas_faltantes, mapeo = procesar_dataframe_excel(df_excel)
                    if columnas_faltantes:
                        with placeholder_tabla.container():
                            st.error(f"❌ No se encontraron las siguientes columnas: {', '.join(columnas_faltantes)}")
                            st.info(f"Columnas detectadas en el Excel: {', '.join(df_excel.columns.tolist())}")
                            st.info("💡 Puedes usar nombres similares. Revisa la plantilla oficial para ver los nombres exactos.")
                    else:
                        with placeholder_tabla.container():
                            with st.expander("🔍 Ver mapeo de columnas detectadas"):
                                for nombre_requerido, nombre_real in mapeo.items():
                                    st.write(f"  • '{nombre_real}' → **{nombre_requerido}**")
                        with placeholder_tabla.container():
                            st.subheader("📊 Vista previa de datos procesados")
                            st.caption("✏️ Los datos ya fueron transformados. Puedes editarlos antes de subir.")
                            df_editado = st.data_editor(
                                df_procesado,
                                num_rows="dynamic",
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "distrito": st.column_config.SelectboxColumn(
                                        "Distrito",
                                        options=["Chorrillos", "San Juan De Miraflores", "Villa el Salvador"],
                                        required=True
                                    ),
                                    "sector": st.column_config.TextColumn("Sector", help="Formateado a 2 dígitos", required=True),
                                    "manzana": st.column_config.TextColumn("Manzana", help="Formateado a 3 dígitos", required=True),
                                    "tipo": st.column_config.SelectboxColumn(
                                        "Tipo",
                                        options=["Ordinario", "Reproceso Ordinario", "Corrección de Calidad",
                                                 "Corrección de Calidad Extraordinaria", "Producción Horas Extras"],
                                        required=True
                                    ),
                                    "estado": st.column_config.SelectboxColumn(
                                        "Estado",
                                        options=["Finalizado", "En Conflicto"],
                                        required=True
                                    ),
                                    "numero_lote": st.column_config.TextColumn("N° Lote"),
                                    "partida": st.column_config.TextColumn("Partida"),
                                    "unidades_catastrales": st.column_config.NumberColumn("Cant. Registros", min_value=0, required=True),
                                    "horas": st.column_config.NumberColumn("Horas Trab.", min_value=0.0, required=True),
                                    "observaciones": st.column_config.TextColumn("Observaciones")
                                },
                                key="editor_masivo_descarga"
                            )
                            # Reforzar campos de texto
                            df_editado['observaciones'] = df_editado['observaciones'].fillna('N/A').replace('', 'N/A')
                            df_editado['partida'] = df_editado['partida'].fillna('N/A').replace('', 'N/A')
                            df_editado['numero_lote'] = df_editado['numero_lote'].fillna('Todos').replace('', 'Todos')
                            df_editado['sector'] = df_editado['sector'].apply(formatear_sector)
                            df_editado['manzana'] = df_editado['manzana'].apply(formatear_manzana)
                            df_editado['numero_lote'] = df_editado['numero_lote'].apply(
                                lambda x: formatear_lote(x) if str(x).strip().lower() != 'todos' else 'Todos'
                            )

                        if not df_editado.empty:
                            with placeholder_estadisticas.container():
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("📊 Registros", len(df_editado))
                                with col2:
                                    st.metric("🏘️ Sectores", df_editado['sector'].nunique())
                                with col3:
                                    st.metric("🏠 Manzanas", df_editado['manzana'].nunique())

            except Exception as e:
                with placeholder_tabla.container():
                    st.error(f"❌ Error al leer el archivo Excel: {str(e)}")
                    st.info("💡 Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls) y que los datos estén en la Hoja1")

        placeholder_boton_masivo = st.empty()
        subir_masivo = placeholder_boton_masivo.button(
            "🚀 Subir Registros Masivos",
            type="primary",
            use_container_width=True,
            key="subir_masivo_descarga",
            disabled=(df_editado is None or df_editado.empty)
        )

        if subir_masivo and df_editado is not None:
            with st.spinner("⏳ Validando datos..."):
                es_valido, mensaje_validacion = validar_datos_masivos(df_editado, fecha_masiva)
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
                        exito, insertados, mensaje = insertar_registros_masivos(df_editado, fecha_masiva, usuario, usuario_activo)
                        if exito:
                            st.success(f"✅ {mensaje}")
                            st.balloons()
                        else:
                            st.error(f"❌ {mensaje}")
                            st.error(f"Se insertaron {insertados} registros antes del error.")

    # ------------------------------------------------------------
    # Función para limpiar todos los placeholders
    # ------------------------------------------------------------
    def limpiar():
        for p in [placeholder1, placeholder2, placeholder3, placeholder4,
                  placeholder5, placeholder6, placeholder7, placeholder_titulo,
                  placeholder_modo,
                  placeholder_fecha, placeholder_distrito, placeholder_sector,
                  placeholder_manzana, placeholder_tipo, placeholder_estado,
                  placeholder_lote, placeholder_partida, placeholder_uc,
                  placeholder_horas, placeholder_obs, placeholder_reporte]:
            if p: p.empty()
        # Limpiar placeholders del modo masivo (si existen)
        if 'placeholder_fecha_masiva' in locals() and placeholder_fecha_masiva:
            placeholder_fecha_masiva.empty()
        if 'placeholder_instrucciones' in locals() and placeholder_instrucciones:
            placeholder_instrucciones.empty()
        if 'placeholder_descarga_plantilla' in locals() and placeholder_descarga_plantilla:
            placeholder_descarga_plantilla.empty()
        if 'placeholder_archivo' in locals() and placeholder_archivo:
            placeholder_archivo.empty()
        if 'placeholder_tabla' in locals() and placeholder_tabla:
            placeholder_tabla.empty()
        if 'placeholder_estadisticas' in locals() and placeholder_estadisticas:
            placeholder_estadisticas.empty()
        if 'placeholder_boton_masivo' in locals() and placeholder_boton_masivo:
            placeholder_boton_masivo.empty()

    # ------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------
    if procesos_btn:
        limpiar()
        st.session_state.Procesos = False
        usuario_activo = obtener_usuario_activo(usuario)
        perfil = str(usuario_activo["perfil"]) if usuario_activo else ""
        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)

    elif historial_btn:
        limpiar()
        st.session_state.Historial = True
        Historial.Historial(usuario, puesto)

    elif capacitacion_btn:
        limpiar()
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif otros_btn:
        limpiar()
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif bonos_btn:
        limpiar()
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif salir_btn:
        limpiar()
        st.session_state.Ingreso = False
        st.session_state.Salir = True
        Salir.Salir()

    elif modo_carga == "📝 Carga Manual (Formulario)" and reporte_btn:
        # Inserción manual idéntica a la original
        marca = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
        usuario_activo = obtener_usuario_activo(usuario)
        if not usuario_activo:
            st.error("No se encontró un usuario activo para generar el reporte.")
            return

        nombre = usuario_activo["nombre"]
        supervisor = usuario_activo["supervisor"]
        semana = fecha.isocalendar()[1]
        año = fecha.isocalendar()[0]
        horas_bi = float(horas)

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
                marca, usuario, nombre, puesto, supervisor, "Descarga Partidas Jurídico",
                fecha, semana, año, distrito, tipo, 0, 0, 0, horas,
                manzana, sector, numero_lote, estado, 0.0, unidades_catastrales, 0, partida,
                0, 0, observaciones, "N/A",
                "N/A", horas_bi, 0.0, "N/A", 0, 0, "N/A", 0
            ],
        )
        st.success("Reporte enviado correctamente")
