from db_core import (
    con,
    hostname,
    database,
    username,
    pwd,
    port_id,
    fetch_df,
    fetch_one,
)


def contraseña(usuario):
    query = """
        SELECT contraseña
        FROM usuarios
        WHERE usuario = %s
          AND estado = 'Activo'
    """
    return fetch_df(query, params=[usuario])


def obtener_usuario_activo(usuario):
    query = """
        SELECT usuario, contraseña, nombre, puesto, perfil, supervisor
        FROM usuarios
        WHERE usuario = %s
          AND estado = 'Activo'
        LIMIT 1
    """
    return fetch_one(query, params=[usuario])
