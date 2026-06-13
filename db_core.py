import pandas as pd
import streamlit as st
import psycopg2
from urllib.parse import urlparse

uri = st.secrets.db_credentials.URI

result = urlparse(uri)
hostname = result.hostname
database = result.path[1:]
username = result.username
pwd = result.password
port_id = result.port

@st.cache_resource
def init_connection():
    """Crea y cachea una única conexión a la base de datos."""
    return psycopg2.connect(
        host=hostname,
        dbname=database,
        user=username,
        password=pwd,
        port=port_id,
    )

def _get_reliable_connection():
    """
    Obtiene una conexión válida, recreándola si está cerrada o rota.
    Mantiene una única conexión pero la regenera automáticamente cuando falla.
    """
    try:
        conn = init_connection()
        # Prueba de actividad (ping ligero)
        conn.cursor().execute("SELECT 1")
        return conn
    except (psycopg2.InterfaceError, psycopg2.OperationalError, AttributeError) as e:
        # La conexión existente no es válida -> forzar recreación
        st.cache_resource.clear()  # Elimina la conexión cacheada
        return init_connection()   # Crea una nueva

def fetch_df(query: str, params=None):
    """Ejecuta una consulta SELECT y devuelve un DataFrame con reconexión automática."""
    for intento in range(2):  # Máximo 2 intentos
        try:
            conn = _get_reliable_connection()
            return pd.read_sql_query(query, con=conn, params=params)
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            if intento == 0:
                st.cache_resource.clear()  # Limpia caché y reintenta
                continue
            else:
                raise e

def fetch_one(query: str, params=None):
    """Devuelve la primera fila de una consulta como diccionario, o None si vacío."""
    df = fetch_df(query, params=params)
    if df.empty:
        return None
    return df.iloc[0].to_dict()

def execute(query: str, params=None):
    """Ejecuta comandos de modificación (INSERT, UPDATE, DELETE) con reconexión automática."""
    for intento in range(2):
        try:
            conn = _get_reliable_connection()
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            cur.close()
            return True
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            if intento == 0:
                st.cache_resource.clear()
                continue
            else:
                raise e
    return False


# ============================================================================
# A partir de aquí, todas tus funciones originales quedan exactamente igual.
# No necesitan ninguna modificación porque ya usan fetch_df, fetch_one y execute.
# ============================================================================

def fetch_operadores_cc(filtro_proceso=None, filtro_subproceso=None, filtro_proceso_anterior=None, filtro_subproceso_anterior=None):
    """
    Obtiene operadores para Control de Calidad con filtros específicos.
    
    Args:
        filtro_proceso: Valor para columna 'proceso'
        filtro_subproceso: Lista de valores para columna 'subproceso' (IN clause)
        filtro_proceso_anterior: Valor para columna 'proceso_anterior'
        filtro_subproceso_anterior: Lista de valores para columna 'subproceso_anterior' (IN clause)
    
    Returns:
        Lista de diccionarios con nombre y usuario
    """
    query = """
        SELECT DISTINCT nombre, usuario
        FROM public.usuarios
        WHERE estado = 'Activo'
          AND activo_en_listas = 'activo'
    """
    
    condiciones = []
    params = []
    
    # Condición 1: proceso y subproceso actuales cumplen filtros
    if filtro_proceso and filtro_subproceso:
        # Si filtro_subproceso es una lista, usar IN; si es string, usar =
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
    
    # Combinar condiciones con OR (cualquiera que cumpla alguna condición)
    if condiciones:
        query += " AND (" + " OR ".join(condiciones) + ")"
    
    query += " ORDER BY nombre"
    
    df = fetch_df(query, params=params)
    return df.to_dict('records') if not df.empty else []


def fetch_rechazos_pendientes(identificador, tipo='nombre', dias=10):
    """
    Obtiene los rechazos pendientes para un operador.
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
            id,
            fecha,
            proceso,
            distrito,
            manzana,
            sector,
            numero_lote,
            rechazados,
            tipo_de_errores,
            estado
        FROM public.registro
        WHERE operador_cc ILIKE %s
          AND estado = 'N/A'
          AND rechazados > '0'          
          AND fecha >= %s
        ORDER BY fecha DESC
    """
    return fetch_df(query, params=[nombre_buscar, fecha_limite_str])


def fetch_rechazos_pendientes_por_usuario(usuario, dias=10):
    """Versión simplificada que usa el usuario"""
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
            id,
            fecha,
            proceso,
            distrito,
            manzana,
            sector,
            numero_lote,
            rechazados,
            tipo_de_errores,
            estado
        FROM public.registro
        WHERE operador_cc ILIKE %s
          AND estado = 'N/A'
          AND rechazados > '0'          
          AND fecha >= %s
        ORDER BY fecha DESC
    """
    return fetch_df(query, params=[nombre_operador, fecha_limite_str])


def actualizar_estado_rechazo(id_registro, nuevo_estado):
    """Solo actualiza estado a 'corregido'"""
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
        print(f"Error: {e}")
        return False


def fetch_registros_corregidos_pendientes(usuario):
    """
    Obtiene los registros con estado 'corregido' para un usuario específico,
    donde el operador_cc no es 'N/A'.
    
    Args:
        usuario: Usuario logueado para filtrar los registros
    
    Returns:
        DataFrame con los registros pendientes de revisión
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
    
    Args:
        id_registro: ID del registro a actualizar
        nuevo_estado: Nuevo estado (por defecto 'revisado')
    
    Returns:
        True si se actualizó correctamente, False en caso contrario
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
        print(f"Error al actualizar estado: {e}")
        return False
