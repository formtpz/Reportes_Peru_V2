# ----- Librerías ---- #

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import io
import Procesos,Historial,Capacitacion,Otros_Registros,Bonos_Extras,Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute

def formatear_sector(valor):
    """Asegura que el sector tenga 2 dígitos (01, 02, etc.)"""
    try:
        return str(int(float(valor))).zfill(2)
    except:
        return str(valor).zfill(2)

def formatear_manzana(valor):
    """Asegura que la manzana tenga 3 dígitos (001, 002, etc.)"""
    try:
        return str(int(float(valor))).zfill(3)
    except:
        return str(valor).zfill(3)

def formatear_lote(valor):
    """
    Asegura que cada número de lote tenga 3 dígitos (001, 002, etc.)
    Soporta:
    - Número individual: "2" → "002"
    - Múltiples lotes: "2, 3, 112, 113" → "002, 003, 112, 113"
    - "Todos" → "Todos"
    - Ya formateados: "002, 003" → "002, 003"
    """
    try:
        valor_str = str(valor).strip()
        
        # Si es vacío o nulo
        if not valor_str or valor_str.lower() == 'nan':
            return 'Todos'
        
        # Si es "Todos", devolver sin cambios
        if valor_str.lower() == 'todos':
            return 'Todos'
        
        # Si contiene comas, procesar cada número por separado
        if ',' in valor_str:
            numeros = []
            for num in valor_str.split(','):
                num = num.strip()
                if num:  # Ignorar vacíos
                    try:
                        numeros.append(str(int(float(num))).zfill(3))
                    except:
                        numeros.append(num)  # Mantener si no es número
            return ', '.join(numeros) if numeros else 'Todos'
        else:
            # Número individual
            return str(int(float(valor_str))).zfill(3)
            
    except:
        # Si todo falla, devolver el valor original
        return str(valor)

def normalizar_horas(valor):
    """Convierte comas a puntos en horas y asegura que sea float"""
    try:
        if isinstance(valor, str):
            valor = valor.replace(',', '.')
        return float(valor)
    except:
        return 0.0

def normalizar_texto(valor, default="N/A"):
    """Convierte valores nulos o vacíos al valor por defecto"""
    if pd.isna(valor) or valor == '' or valor is None:
        return default
    return str(valor)

def buscar_columnas_por_coincidencia(df):
    """
    Busca las columnas requeridas por coincidencia de nombres
    Retorna un diccionario mapeando nombre_requerido -> nombre_real_en_excel
    """
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
    """
    Procesa el DataFrame del Excel aplicando todas las transformaciones
    """
    # Buscar columnas por coincidencia
    mapeo_columnas = buscar_columnas_por_coincidencia(df)
    
    # Verificar columnas encontradas
    columnas_requeridas = [
        'distrito', 'sector', 'manzana', 'tipo', 'estado', 
        'numero_lote', 'partida', 'unidades_catastrales', 'horas', 'observaciones'
    ]
    
    columnas_faltantes = [col for col in columnas_requeridas if col not in mapeo_columnas]
    
    if columnas_faltantes:
        return None, columnas_faltantes, mapeo_columnas
    
    # Crear nuevo DataFrame con nombres estandarizados
    df_procesado = pd.DataFrame()
    
    for nombre_requerido, nombre_real in mapeo_columnas.items():
        df_procesado[nombre_requerido] = df[nombre_real]
    
    # Aplicar transformaciones
    # Sector: convertir a texto con 2 dígitos
    df_procesado['sector'] = df_procesado['sector'].apply(formatear_sector)
    
    # Manzana: convertir a texto con 3 dígitos
    df_procesado['manzana'] = df_procesado['manzana'].apply(formatear_manzana)
    
    # Número de lote: formatear a 3 dígitos (excepto "Todos")
    df_procesado['numero_lote'] = df_procesado['numero_lote'].apply(
        lambda x: formatear_lote(x) if str(x).strip().lower() != 'todos' else 'Todos'
    )
    
    # Horas: normalizar (comas a puntos) y convertir a float
    df_procesado['horas'] = df_procesado['horas'].apply(normalizar_horas)
    
    # Unidades catastrales: asegurar que sea número entero
    df_procesado['unidades_catastrales'] = pd.to_numeric(
        df_procesado['unidades_catastrales'].apply(
            lambda x: str(x).replace(',', '.') if isinstance(x, str) else x
        ), 
        errors='coerce'
    ).fillna(0).astype(int)
    
    # Observaciones: reemplazar nulos por "N/A"
    df_procesado['observaciones'] = df_procesado['observaciones'].apply(
        lambda x: normalizar_texto(x, "N/A")
    )
    
    # Partida: reemplazar nulos por "N/A"
    df_procesado['partida'] = df_procesado['partida'].apply(
        lambda x: normalizar_texto(x, "N/A")
    )
    
    # Numero_lote: reemplazar nulos por "Todos"
    df_procesado['numero_lote'] = df_procesado['numero_lote'].apply(
        lambda x: normalizar_texto(x, "Todos")
    )
    
    return df_procesado, [], mapeo_columnas

def validar_datos_masivos(df, fecha_seleccionada):
    """
    Valida los datos antes de la inserción masiva
    Retorna (es_valido, mensaje_error)
    """
    errores = []
    
    # Validar que no esté vacío
    if df.empty:
        return False, "La tabla está vacía. No hay datos para procesar."
    
    # Validar valores nulos en columnas requeridas
    columnas_requeridas = ['distrito', 'sector', 'manzana', 'tipo', 'estado']
    for col in columnas_requeridas:
        nulos = df[col].isnull().sum()
        if nulos > 0:
            errores.append(f"La columna '{col}' tiene {nulos} valores nulos")
    
    # Validar distritos válidos
    distritos_validos = ["Chorrillos", "San Juan De Miraflores", "Villa el Salvador"]
    distritos_invalidos = df[~df['distrito'].isin(distritos_validos)]
    if not distritos_invalidos.empty:
        filas_invalidas = distritos_invalidos.index.tolist()
        errores.append(f"Hay {len(distritos_invalidos)} registros con distrito inválido en filas: {filas_invalidas}")
    
    # Validar tipos válidos
    tipos_validos = ["Ordinario", "Reproceso Ordinario", "Corrección de Calidad", 
                     "Corrección de Calidad Extraordinaria", "Producción Horas Extras"]
    tipos_invalidos = df[~df['tipo'].isin(tipos_validos)]
    if not tipos_invalidos.empty:
        filas_invalidas = tipos_invalidos.index.tolist()
        errores.append(f"Hay {len(tipos_invalidos)} registros con tipo inválido en filas: {filas_invalidas}")
    
    # Validar estados válidos
    estados_validos = ["Finalizado", "En Conflicto"]
    estados_invalidos = df[~df['estado'].isin(estados_validos)]
    if not estados_invalidos.empty:
        filas_invalidas = estados_invalidos.index.tolist()
        errores.append(f"Hay {len(estados_invalidos)} registros con estado inválido en filas: {filas_invalidas}")
    
    # Validar que horas sea numérico y positivo
    horas_invalidas = df[df['horas'] < 0]
    if not horas_invalidas.empty:
        errores.append(f"Hay {len(horas_invalidas)} registros con horas negativas")
    
    # Validar que unidades_catastrales sea positivo
    uc_invalidas = df[df['unidades_catastrales'] < 0]
    if not uc_invalidas.empty:
        errores.append(f"Hay {len(uc_invalidas)} registros con unidades catastrales negativas")
    
    if errores:
        return False, "\n".join(errores)
    
    return True, "Datos válidos"

def insertar_registros_masivos(df, fecha_seleccionada, usuario, usuario_activo):
    """
    Inserta múltiples registros usando la función execute existente
    Retorna (exito, registros_insertados, mensaje)
    """
    try:
        marca = datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
        nombre = usuario_activo["nombre"]
        supervisor = usuario_activo["supervisor"]
        puesto = usuario_activo.get("puesto", "")
        
        # Calcular semana y año de la fecha seleccionada
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
                    marca, usuario, nombre, puesto, supervisor, "Precampo Jurídico", 
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

def Precampo_Juridico(usuario,puesto):

  # ----- Conexión, Botones y Memoria ---- #
  uri=st.secrets.db_credentials.URI

  # Inicializar TODOS los placeholders como None
  placeholder_fecha_masiva = None
  placeholder_instrucciones_masivo = None
  placeholder_descarga = None
  placeholder_archivo = None
  placeholder_tabla_masiva = None
  placeholder_boton_masivo = None
  placeholder_estadisticas = None

  placeholder1_3= st.sidebar.empty()
  titulo= placeholder1_3.title("Menú")

  placeholder2_3 = st.sidebar.empty()
  procesos_3 = placeholder2_3.button("Procesos",key="procesos_3")

  placeholder3_3 = st.sidebar.empty()
  historial_3 = placeholder3_3.button("Historial",key="historial_3")

  placeholder4_3 = st.sidebar.empty()
  capacitacion_3 = placeholder4_3.button("Capacitaciones",key="capacitacion_3")

  placeholder5_3 = st.sidebar.empty()
  otros_registros_3 = placeholder5_3.button("Otros Registros",key="otros_registros_3")

  placeholder6_3 = st.sidebar.empty()
  bonos_extras_3 = placeholder6_3.button("Bonos y Horas Extras",key="bonos_extras_3")

  placeholder7_3 = st.sidebar.empty()
  salir_3 = placeholder7_3.button("Salir",key="salir_3")

  # ----- Selector de modo de carga ----- #
  placeholder_modo = st.empty()
  modo_carga = placeholder_modo.radio(
      "Selecciona el modo de carga:",
      options=["📝 Carga Manual (Formulario)", "📋 Carga Masiva (Subir Excel)"],
      key="modo_carga_precampo"
  )

  placeholder8_3 = st.empty()
  Precampo_Juridico_3 = placeholder8_3.title("Precampo Jurídico")

  # Inicializar variables del formulario manual como None
  placeholder9_3 = None
  placeholder10_3 = None
  placeholder12_3 = None
  placeholder13_3 = None
  placeholder15_3 = None
  placeholder16_3 = None
  placeholder18_3 = None
  placeholder19_3 = None
  placeholder20_3 = None
  placeholder21_3 = None
  placeholder22_3 = None
  placeholder23_3 = None
  
  fecha_3 = None
  distrito_3 = None
  sector_3 = None
  manzana_3 = None
  tipo_3 = None
  estado_3 = None
  numero_lote_3 = None
  partida_3 = None
  unidades_catastrales_3 = None
  horas_3 = None
  observaciones_3 = None
  reporte_3 = None

  # ============================================
  # MODO DE CARGA MANUAL (CÓDIGO ORIGINAL)
  # ============================================
  if modo_carga == "📝 Carga Manual (Formulario)":
    
    default_date_3 = datetime.now(pytz.timezone('America/Guatemala'))

    placeholder9_3= st.empty()
    fecha_3= placeholder9_3.date_input("Fecha",value=default_date_3,key="fecha_3")
     
    placeholder10_3= st.empty()
    distrito_3= placeholder10_3.selectbox("Distrito", options=("Chorrillos","San Juan De Miraflores","Villa el Salvador"), key="distrito_3")
    
    placeholder12_3= st.empty()
    sector_3= placeholder12_3.selectbox("Sector", options=("01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","46","47","48","49","50","51","52","53","54","55","56","57","58","59","60","61","62","63","64","65","66","67","68","69","70","71","72","73","74","75","76","77","78","79","80","81","82","83","84","85","86","87","88","89","90","91","92","93","94","95","96","97","98","99","100","101","102","103","104","105","106","107","108","109","110","111","112","113","114","115","116","117","118","119","120"), key="sector_3")

    placeholder13_3= st.empty()
    manzana_3= placeholder13_3.selectbox("Manzana", options=("001","002","003","004","005","006","007","008","009","010","011","012","013","014","015","016","017","018","019","020","021","022","023","024","025","026","027","028","029","030","031","032","033","034","035","036","037","038","039","040","041","042","043","044","045","046","047","048","049","050","051","052","053","054","055","056","057","058","058","059","060","061","062","063","064","065","066","067","068","069","070","071","072","073","074","075","076","077","078","079","080","081","082","083","084","085","086","087","088","089","090","091","092","093","094","095","096","097","098","099","100","101","102","103","104","105","106","107","108","109","110","111","112","113","114","115","116","117","118","119","120"),key="manzana_3")
    
    placeholder15_3= st.empty()
    tipo_3= placeholder15_3.selectbox("Tipo", options=("Ordinario","Reproceso Ordinario","Corrección de Calidad","Corrección de Calidad Extraordinaria","Producción Horas Extras"), key="tipo_3")
    
    placeholder16_3= st.empty()
    estado_3= placeholder16_3.selectbox("Estado" , options=("Finalizado","En Conflicto"),key="estado_3")
    
    lotes = ["Todos"] + [f"{i:03d}" for i in range(1,249)]
    
    placeholder18_3 = st.empty()
    
    numero_lote_3 = placeholder18_3.multiselect(
        "Número de Lote",
        options=lotes,
        key="numero_lote_3"
    )
    
    if "Todos" in numero_lote_3:
        numero_lote_3 = ["Todos"]
    
    numero_lote_3 = ",".join(numero_lote_3) 
    
    placeholder19_3= st.empty()
    partida_3= placeholder19_3.text_input("Número de Partida",value="N/A", max_chars=60,key="partida_3")
         
    placeholder20_3= st.empty()
    unidades_catastrales_3= placeholder20_3.number_input("Cantidad de Registros",min_value=0,step=1,key="unidades_catastrales_3")
    
    placeholder21_3= st.empty()
    horas_3= placeholder21_3.number_input("Cantidad de Horas Trabajadas en el Proceso",min_value=0.0,key="horas_3")

    placeholder22_3= st.empty()
    observaciones_3= placeholder22_3.text_input("Observaciones",value="N/A", max_chars=60, key="observaciones_3")
   
    placeholder23_3 = st.empty()
    reporte_3 = placeholder23_3.button("Generar Reporte",key="reporte_3")

  # ============================================
  # MODO DE CARGA MASIVA (SUBIR EXCEL)
  # ============================================
  else:
    
    # Fecha común para todos los registros
    placeholder_fecha_masiva = st.empty()
    fecha_masiva = placeholder_fecha_masiva.date_input(
        "📅 Fecha para todos los registros",
        value=datetime.now(pytz.timezone('America/Guatemala')),
        key="fecha_masiva_precampo"
    )
    
    # Instrucciones dentro de placeholder
    placeholder_instrucciones_masivo = st.empty()
    with placeholder_instrucciones_masivo.container():
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
    
    # Enlace de descarga de plantilla desde GitHub
    placeholder_descarga = st.empty()
    with placeholder_descarga.container():
        st.markdown("### 📥 Plantilla oficial")
        
        # URL directa al archivo raw en GitHub
        url_plantilla = "https://raw.githubusercontent.com/formtpz/Reportes_Peru_V2/main/docs/precampojuridico.xlsx"
        
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
            st.caption("Descarga el machote oficial `precampojuridico.xlsx`")
            st.caption(f"🔗 [Enlace directo]({url_plantilla})")
    
    # Subir archivo Excel
    placeholder_archivo = st.empty()
    archivo_excel = placeholder_archivo.file_uploader(
        "📁 Subir archivo Excel con datos",
        type=['xlsx', 'xls'],
        key="archivo_excel_precampo",
        help="Selecciona el archivo Excel con los datos a cargar (Hoja1)"
    )
    
    df_editado = None
    placeholder_tabla_masiva = st.empty()
    placeholder_estadisticas = st.empty()
    
    if archivo_excel is not None:
        try:
            # Leer el archivo Excel (Hoja1)
            df_excel = pd.read_excel(archivo_excel, sheet_name=0)
            
            if df_excel.empty:
                with placeholder_tabla_masiva.container():
                    st.error("❌ El archivo Excel está vacío")
            else:
                # Procesar el DataFrame
                df_procesado, columnas_faltantes, mapeo = procesar_dataframe_excel(df_excel)
                
                if columnas_faltantes:
                    with placeholder_tabla_masiva.container():
                        st.error(f"❌ No se encontraron las siguientes columnas: {', '.join(columnas_faltantes)}")
                        st.info(f"Columnas detectadas en el Excel: {', '.join(df_excel.columns.tolist())}")
                        st.info("💡 Puedes usar nombres similares. Revisa la plantilla oficial para ver los nombres exactos.")
                else:
                    # Mostrar mapeo de columnas
                    with placeholder_tabla_masiva.container():
                        with st.expander("🔍 Ver mapeo de columnas detectadas"):
                            st.write("Columnas encontradas en el Excel y su correspondencia:")
                            for nombre_requerido, nombre_real in mapeo.items():
                                st.write(f"  • '{nombre_real}' → **{nombre_requerido}**")
                    
                    # Mostrar vista previa editable
                    with placeholder_tabla_masiva.container():
                        st.subheader("📊 Vista previa de datos procesados")
                        st.caption("✏️ Los datos ya fueron transformados. Puedes editarlos antes de subir.")
                        
                        # Tabla editable con los datos procesados
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
                                "sector": st.column_config.TextColumn(
                                    "Sector",
                                    help="Formateado a 2 dígitos",
                                    required=True
                                ),
                                "manzana": st.column_config.TextColumn(
                                    "Manzana",
                                    help="Formateado a 3 dígitos",
                                    required=True
                                ),
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
                                "numero_lote": st.column_config.TextColumn(
                                    "N° Lote",
                                    help="Formateado a 3 dígitos"
                                ),
                                "partida": st.column_config.TextColumn("Partida"),
                                "unidades_catastrales": st.column_config.NumberColumn(
                                    "Cant. Registros",
                                    min_value=0,
                                    required=True
                                ),
                                "horas": st.column_config.NumberColumn(
                                    "Horas Trab.",
                                    min_value=0.0,
                                    required=True
                                ),
                                "observaciones": st.column_config.TextColumn("Observaciones")
                            },
                            key="editor_masivo_precampo"
                        )
                        
                        # ⚡ REFORZAR: Asegurar que los campos de texto no tengan nulos
                        df_editado['observaciones'] = df_editado['observaciones'].fillna('N/A').replace('', 'N/A')
                        df_editado['partida'] = df_editado['partida'].fillna('N/A').replace('', 'N/A')
                        df_editado['numero_lote'] = df_editado['numero_lote'].fillna('Todos').replace('', 'Todos')
                        
                        # ⚡ También asegurar que sector y manzana estén formateados
                        df_editado['sector'] = df_editado['sector'].apply(formatear_sector)
                        df_editado['manzana'] = df_editado['manzana'].apply(formatear_manzana)
                        df_editado['numero_lote'] = df_editado['numero_lote'].apply(
                            lambda x: formatear_lote(x) if str(x).strip().lower() != 'todos' else 'Todos'
                        )
                    
                    # Estadísticas
                    if not df_editado.empty:
                        with placeholder_estadisticas.container():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Registros", len(df_editado))
                            with col2:
                                sectores_unicos = df_editado['sector'].unique()
                                st.metric("🏘️ Sectores", len(sectores_unicos))
                            with col3:
                                manzanas_unicas = df_editado['manzana'].unique()
                                st.metric("🏠 Manzanas", len(manzanas_unicas))
        
        except Exception as e:
            with placeholder_tabla_masiva.container():
                st.error(f"❌ Error al leer el archivo Excel: {str(e)}")
                st.info("💡 Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls) y que los datos estén en la Hoja1")
    
    # Botón de carga masiva
    placeholder_boton_masivo = st.empty()
    subir_masivo = placeholder_boton_masivo.button(
        "🚀 Subir Registros Masivos", 
        type="primary", 
        use_container_width=True,
        key="subir_masivo_precampo",
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
                    exito, insertados, mensaje = insertar_registros_masivos(
                        df_editado, fecha_masiva, usuario, usuario_activo
                    )
                    
                    if exito:
                        st.success(f"✅ {mensaje}")
                        
                        
                    else:
                        st.error(f"❌ {mensaje}")
                        st.error(f"Se insertaron {insertados} registros antes del error.")

  # ============================================
  # FUNCIÓN PARA LIMPIAR PLACEHOLDERS
  # ============================================
  def limpiar_placeholders():
      """Limpia todos los placeholders posibles"""
      placeholder1_3.empty()
      placeholder2_3.empty()
      placeholder3_3.empty()
      placeholder4_3.empty()
      placeholder5_3.empty()
      placeholder6_3.empty()
      placeholder7_3.empty()
      placeholder8_3.empty()
      placeholder_modo.empty()
      
      # Limpiar placeholders del formulario manual
      if placeholder9_3: placeholder9_3.empty()
      if placeholder10_3: placeholder10_3.empty()
      if placeholder12_3: placeholder12_3.empty()
      if placeholder13_3: placeholder13_3.empty()
      if placeholder15_3: placeholder15_3.empty()
      if placeholder16_3: placeholder16_3.empty()
      if placeholder18_3: placeholder18_3.empty()
      if placeholder19_3: placeholder19_3.empty()
      if placeholder20_3: placeholder20_3.empty()
      if placeholder21_3: placeholder21_3.empty()
      if placeholder22_3: placeholder22_3.empty()
      if placeholder23_3: placeholder23_3.empty()
      
      # Limpiar placeholders de carga masiva
      if placeholder_fecha_masiva: placeholder_fecha_masiva.empty()
      if placeholder_instrucciones_masivo: placeholder_instrucciones_masivo.empty()
      if placeholder_descarga: placeholder_descarga.empty()
      if placeholder_archivo: placeholder_archivo.empty()
      if placeholder_tabla_masiva: placeholder_tabla_masiva.empty()
      if placeholder_estadisticas: placeholder_estadisticas.empty()
      if placeholder_boton_masivo: placeholder_boton_masivo.empty()

  # ----- Procesos ---- #
    
  if procesos_3:
    limpiar_placeholders()
    st.session_state.Procesos=False
    st.session_state.Postcampo=False

    usuario_activo = obtener_usuario_activo(usuario)
    perfil = str(usuario_activo["perfil"]) if usuario_activo else ""

    if perfil=="1":        
        Procesos.Procesos1(usuario,puesto)
    elif perfil=="2":        
        Procesos.Procesos2(usuario,puesto)   
    elif perfil=="3":  
        Procesos.Procesos3(usuario,puesto)       

  #----- Historial ---- #
    
  elif historial_3:
    limpiar_placeholders()
    st.session_state.Postcampo=False
    st.session_state.Historial=True
    Historial.Historial(usuario,puesto)   

  # ----- Capacitación ---- #
    
  elif capacitacion_3:
    limpiar_placeholders()
    st.session_state.Postcampo=False
    st.session_state.Capacitacion=True
    Capacitacion.Capacitacion(usuario,puesto)

  # ----- Otros Registros ---- #
    
  elif otros_registros_3:
    limpiar_placeholders()
    st.session_state.Postcampo=False
    st.session_state.Otros_Registros=True
    Otros_Registros.Otros_Registros(usuario,puesto)

  # ----- Bonos y Horas Extras ---- #
    
  elif bonos_extras_3:
    limpiar_placeholders()
    st.session_state.Postcampo=False
    st.session_state.Bonos_Extras=True
    Bonos_Extras.Bonos_Extras(usuario,puesto)    

  # ----- Salir ---- #
    
  elif salir_3:
    limpiar_placeholders()
    st.session_state.Ingreso = False
    st.session_state.Postcampo=False
    st.session_state.Salir=True
    Salir.Salir()

  elif modo_carga == "📝 Carga Manual (Formulario)" and reporte_3:

    marca_3= datetime.now(pytz.timezone('America/Guatemala')).strftime("%Y-%m-%d %H:%M:%S")
    
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
        marca_3, usuario, nombre_3, puesto, supervisor_3, "Precampo Jurídico", fecha_3, semana_3, año_3, distrito_3, tipo_3, 0, 0, 0, horas_3,
        manzana_3, sector_3, numero_lote_3, estado_3, 0.0, unidades_catastrales_3, 0, partida_3, 0, 0, observaciones_3, "N/A",
        "N/A", horas_bi, 0.0, "N/A", 0, 0, "N/A", 0
      ],
    )
    st.success('Reporte enviado correctamente')
