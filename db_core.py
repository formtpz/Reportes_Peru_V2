import pandas as pd
import streamlit as st
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
import logging

# Configurar logging (opcional, útil para depuración)
logging.basicConfig(level=logging.INFO)

# Leer credenciales desde los secretos de Streamlit
uri = st.secrets.db_credentials.URI
result = urlparse(uri)
hostname = result.hostname
database = result.path[1:]
username = result.username
pwd = result.password
port_id = result.port

# -------------------------------------------------------------------
# Gestión de conexión con recarga automática si se cierra
# -------------------------------------------------------------------
@st.cache_resource
def init_connection():
    """Crea y retorna una nueva conexión a la base de datos."""
    return psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id,
    )

def get_connection():
    """
    Obtiene la conexión cacheada y verifica que esté abierta.
    Si está cerrada, la recrea automáticamente.
    """
    conn = init_connection()
    if conn.closed:
        logging.info("Conexión cerrada detectada. Recreando...")
        # Limpiar la caché de Streamlit para forzar la recreación
        init_connection.clear()
        conn = init_connection()
    return conn

# -------------------------------------------------------------------
# Funciones genéricas para consultas
# -------------------------------------------------------------------
def fetch_df(query: str, params=None):
    """Ejecuta una consulta SELECT y retorna un DataFrame."""
    conn = get_connection()
    return pd.read_sql_query(query, con=conn, params=params)

def fetch_one(query: str, params=None):
    """Retorna la primera fila como diccionario, o None si no hay resultados."""
    df = fetch_df(query, params=params)
    if df.empty:
        return None
    return df.iloc[0].to_dict()

def execute(query: str, params=None):
    """Ejecuta una consulta que modifica datos (INSERT, UPDATE, DELETE)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.error(f"Error en execute: {e}")
        raise
    finally:
        cur.close()

# -------------------------------------------------------------------
# Funciones nuevas para INSERT con RETURNING y bulk inserts
# -------------------------------------------------------------------
def execute_returning(query: str, params=None):
    """
    Ejecuta un INSERT/UPDATE/DELETE que incluya la cláusula RETURNING
    y devuelve el valor de la primera columna de la primera fila resultante.

    Ejemplo:
        nuevo_id = execute_returning(
            "INSERT INTO public.registro (...) VALUES (...) RETURNING id",
            params=[...]
        )
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        resultado = cur.fetchone()
        conn.commit()
        return resultado[0] if resultado else None
    except Exception as e:
        conn.rollback()
        logging.error(f"Error en execute_returning: {e}")
        raise
    finally:
        cur.close()

def execute_many(query: str, params_list):
    """
    Ejecuta múltiples INSERT/UPDATE usando execute_values de psycopg2.
    Es mucho más rápido que hacer N execute() individuales.

    IMPORTANTE: 'query' debe contener exactamente UN '%s' en la cláusula VALUES
    donde irá la lista de tuplas. execute_values lo reemplaza por la lista
    completa de valores.

    Ejemplo:
        execute_many(
            \"\"\"INSERT INTO public.registros_qa1 
               (id_registro, crc, aprobados, rechazados) 
               VALUES %s\"\"\",
            [(1, 'CRC1', 1, 0), (1, 'CRC2', 0, 1)]
        )
    """
    if not params_list:
        return 0
    conn = get_connection()
    cur = conn.cursor()
    try:
        execute_values(cur, query, params_list)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        logging.error(f"Error en execute_many: {e}")
        raise
    finally:
        cur.close()

def insertar_registro_con_detalle_qa(datos_registro: dict, detalles_qa: list):
    """
    Inserta un registro en public.registro y sus detalles en public.registros_qa1
    de forma atómica (una sola transacción). Si falla cualquier paso, hace rollback.

    Args:
        datos_registro: dict con {columna: valor} para el INSERT en registro.
        detalles_qa: lista de tuplas (crc, aprobados, rechazados).

    Returns:
        id del registro insertado en public.registro.
    """
    columnas = ', '.join(datos_registro.keys())
    placeholders = ', '.join(['%s'] * len(datos_registro))
    valores = list(datos_registro.values())

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO public.registro ({columnas}) VALUES ({placeholders}) RETURNING id",
            valores
        )
        fila = cur.fetchone()
        if not fila:
            raise Exception("No se pudo obtener el id del registro insertado.")
        id_registro = fila[0]

        if detalles_qa:
            execute_values(
                cur,
                "INSERT INTO public.registros_qa1 (id_registro, crc, aprobados, rechazados) VALUES %s",
                [(id_registro, str(crc).strip(), int(ap), int(re)) for crc, ap, re in detalles_qa]
            )

        conn.commit()
        return id_registro
    except Exception as e:
        conn.rollback()
        logging.error(f"Error en insertar_registro_con_detalle_qa: {e}")
        raise
    finally:
        cur.close()

# -------------------------------------------------------------------
# Funciones específicas de la lógica de negocio
# -------------------------------------------------------------------
def fetch_operadores_cc(filtro_proceso=None, filtro_subproceso=None, 
                        filtro_proceso_anterior=None, filtro_subproceso_anterior=None):
    """
    Obtiene operadores para Control de Calidad con filtros específicos.
    
    Args:
        filtro_proceso: Valor para columna 'proceso'
        filtro_subproceso: Lista de valores para columna 'subproceso' (IN clause)
        filtro_proceso_anterior: Valor para columna 'proceso_anterior'
        filtro_subproceso_anterior: Lista de valores para columna 'subproceso_anterior'
    
    Returns:
        Lista de diccionarios con nombre y usuario
    """
    query = """
        SELECT DISTINCT nombre, usuario
        FROM public.usuarios
        WHERE activo_en_listas = 'activo'
    """
    
    condiciones = []
    params = []
    
    # Condición 1: proceso y subproceso actuales cumplen filtros
    if filtro_proceso and filtro_subproceso:
        if isinstance(filtro_subproceso, list):
            cond1 = "(proceso = %s AND subproceso IN %s)"
            params.extend([filtro_proceso, tuple(filtro_subproceso)])
        else:
            cond1 = "(proceso = %s AND subproceso = %s)"
            params.extend([filtro_proceso, filtro_subproceso])
        condiciones.append(cond1)
    
    # Condición 2: proceso_anterior y subproceso_anterior cumplen filtros
    if filtro_proceso_anterior and filtro_subproceso_anterior:
        if isinstance(filtro_subproceso_anterior, list):
            cond2 = "(proceso_anterior = %s AND subproceso_anterior IN %s)"
            params.extend([filtro_proceso_anterior, tuple(filtro_subproceso_anterior)])
        else:
            cond2 = "(proceso_anterior = %s AND subproceso_anterior = %s)"
            params.extend([filtro_proceso_anterior, filtro_subproceso_anterior])
        condiciones.append(cond2)
    
    # Combinar condiciones con OR
    if condiciones:
        query += " AND (" + " OR ".join(condiciones) + ")"
    
    query += " ORDER BY nombre"
    
    df = fetch_df(query, params=params)
    return df.to_dict('records') if not df.empty else []

def fetch_rechazos_pendientes(identificador, tipo='nombre', dias=10):
    """
    Obtiene los rechazos pendientes para un operador.
    Puede buscar por nombre o por usuario.
    """
    from datetime import datetime, timedelta
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    fecha_limite_str = fecha_limite.strftime('%Y-%m-%d')
    
    if tipo == 'usuario':
        query_nombre = """
            SELECT nombre FROM public.usuarios WHERE usuario = %s AND estado = 'Activo'
        """
        df_nombre = fetch_df(query_nombre, params=[identificador])
        if df_nombre.empty:
            return pd.DataFrame()
        nombre_buscar = df_nombre['nombre'].iloc[0]
    else:
        nombre_buscar = identificador
    
    query = """
        SELECT 
            id, fecha, proceso, distrito, manzana, sector, numero_lote,
            rechazados, tipo_de_errores, estado
        FROM public.registro
        WHERE operador_cc ILIKE %s
          AND estado = 'N/A'
          AND rechazados > '0'          
          AND fecha >= %s
        ORDER BY fecha DESC
    """
    return fetch_df(query, params=[nombre_buscar, fecha_limite_str])

def fetch_rechazos_pendientes_por_usuario(usuario, dias=10):
    """Versión simplificada que obtiene rechazos usando el nombre de usuario."""
    from datetime import datetime, timedelta
    
    query_nombre = """
        SELECT nombre FROM public.usuarios WHERE usuario = %s AND estado = 'Activo'
    """
    df_nombre = fetch_df(query_nombre, params=[usuario])
    
    if df_nombre.empty:
        return pd.DataFrame()
    
    nombre_operador = df_nombre['nombre'].iloc[0]
    
    fecha_limite = datetime.now() - timedelta(days=dias)
    fecha_limite_str = fecha_limite.strftime('%Y-%m-%d')
    
    query = """
        SELECT 
            id, fecha, proceso, distrito, manzana, sector, numero_lote,
            rechazados, tipo_de_errores, estado
        FROM public.registro
        WHERE operador_cc ILIKE %s
          AND estado = 'N/A'
          AND rechazados > '0'          
          AND fecha >= %s
        ORDER BY fecha DESC
    """
    return fetch_df(query, params=[nombre_operador, fecha_limite_str])

def actualizar_estado_rechazo(id_registro, nuevo_estado):
    """Actualiza estado a 'corregido' solo si estaba 'N/A'."""
    if nuevo_estado != 'corregido':
        return False
    
    query = """
        UPDATE public.registro
        SET estado = %s
        WHERE id = %s
          AND estado = 'N/A'
    """
    try:
        execute(query, params=[nuevo_estado, id_registro])
        return True
    except Exception as e:
        logging.error(f"Error en actualizar_estado_rechazo: {e}")
        return False

def fetch_registros_corregidos_pendientes(usuario):
    """
    Obtiene los registros con estado 'corregido' para un usuario específico,
    donde el operador_cc no es 'N/A'.
    """
    query = """
        SELECT id, marca, fecha, distrito, manzana, sector, numero_lote, 
               operador_cc, tipo_de_errores, estado
        FROM public.registro
        WHERE usuario = %s 
          AND operador_cc != 'N/A' 
          AND estado = 'corregido'
        ORDER BY marca DESC
    """
    return fetch_df(query, params=[usuario])

def actualizar_estado_revision(id_registro, nuevo_estado='revisado'):
    """
    Actualiza el estado de un registro a 'revisado' solo si actualmente está 'corregido'.
    """
    if nuevo_estado != 'revisado':
        return False
    
    query = """
        UPDATE public.registro
        SET estado = %s
        WHERE id = %s
          AND estado = 'corregido'
    """
    try:
        execute(query, params=[nuevo_estado, id_registro])
        return True
    except Exception as e:
        logging.error(f"Error al actualizar estado revisión: {e}")
        return False

# -------------------------------------------------------------------
# Compatibilidad con código antiguo que hacía: from db_core import con
# -------------------------------------------------------------------
con = get_connection()
