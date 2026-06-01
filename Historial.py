# ----- Librerías ---- #
import numpy as np
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# Importaciones de módulos de navegación
import Procesos, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from db_core import fetch_df

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES DE DATOS
# -------------------------------------------------------------------

def cargar_datos_supervisor(fecha_inicio, fecha_fin, personal, proceso, tipo, nombre_usuario):
    """Carga los datos para el perfil Supervisor/Coordinador según filtros."""
    base_r = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               cast(lotes as float), cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )
    base_c = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, tema,
               cast(horas as float), observaciones, reporte
        FROM capacitaciones
        WHERE fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )
    base_o = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )

    data_r = base_r.copy()
    data_c = base_c.copy()
    data_o = base_o.copy()

    if personal == "Operarios":
        data_r = data_r[data_r["puesto"] == "Operario Catastral"]
        data_c = data_c[data_c["puesto"] == "Operario Catastral"]
        data_o = data_o[data_o["puesto"] == "Operario Catastral"]
    elif personal == "Profesional Jurídico":
        data_r = data_r[data_r["puesto"] == "Profesional Jurídico"]
        data_c = data_c[data_c["puesto"] == "Profesional Jurídico"]
        data_o = data_o[data_o["puesto"] == "Profesional Jurídico"]
    elif personal == "Propio":
        data_r = data_r[data_r["nombre"] == nombre_usuario]
        data_c = data_c[data_c["nombre"] == nombre_usuario]
        data_o = data_o[data_o["nombre"] == nombre_usuario]
    elif personal == "Personal Asignado":
        data_r = data_r[data_r["supervisor"] == nombre_usuario]
        data_c = data_c[data_c["supervisor"] == nombre_usuario]
        data_o = data_o[data_o["supervisor"] == nombre_usuario]

    if proceso != "Todos":
        data_r = data_r[data_r["proceso"] == proceso]
    if tipo != "Todos":
        data_r = data_r[data_r["tipo"] == tipo]

    return data_r, data_c, data_o


def cargar_datos_operario(usuario, fecha_inicio, fecha_fin, proceso, tipo, nombre_completo):
    condiciones = ["usuario = %s"]
    params_where = [usuario]
    if proceso != "Todos":
        condiciones.append("proceso = %s")
        params_where.append(proceso)
    if tipo != "Todos":
        condiciones.append("tipo = %s")
        params_where.append(tipo)

    where_clause = " AND ".join(condiciones)
    params = params_where + [fecha_inicio, fecha_fin]

    data_1_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               cast(lotes as float), cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE {where_clause} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=params
    )

    data_8_r = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               cast(lotes as float), cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
          AND tipo NOT IN ('Producción Horas Extras', 'Inspección Horas Extras', 'Reproceso Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_6_r = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               cast(lotes as float), cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
          AND tipo IN ('Producción Horas Extras', 'Inspección Horas Extras', 'Reproceso Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )

    data_5_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               cast(lotes as float), cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE operador_cc = %s AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[nombre_completo, fecha_inicio, fecha_fin]
    )

    data_1_c = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, tema,
               cast(horas as float), observaciones, reporte
        FROM capacitaciones
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_1_o = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_6_o = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
          AND motivo IN ('Horas Extra', 'Horas Extra Apoyo Otros Proyectos', 'Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_9_o = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
          AND motivo NOT IN ('Reposición de tiempo', 'Horas Extra', 'Horas Extra Apoyo Otros Proyectos', 'Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_7_o = fetch_df(
        """
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND fecha::date >= %s AND fecha::date <= %s
          AND motivo = 'Reposición de tiempo'
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )

    return data_1_r, data_8_r, data_6_r, data_5_r, data_1_c, data_1_o, data_6_o, data_9_o, data_7_o


# -------------------------------------------------------------------
# FUNCIONES DE PROCESAMIENTO DE DATOS
# -------------------------------------------------------------------

# RESUMEN DE HORAS
def generar_resumen_horas(data_r, data_c, data_o): #FILTROS 
    data_8_r = data_r[~data_r["tipo"].isin(["Producción Horas Extras", "Inspección Horas Extras", "Reproceso Horas Extras"])].copy() #Produccion menos ...
    data_6_r = data_r[data_r["tipo"].isin(["Producción Horas Extras", "Inspección Horas Extras", "Reproceso Horas Extras"])].copy() #Produccion igual a ....
    data_6_o = data_o[data_o["motivo"].isin(["Horas Extra", "Horas Extra Apoyo Otros Proyectos", "Horas Extras"])].copy() #Otros igual a ...
    data_7_o = data_o[data_o["motivo"] == "Reposición de tiempo"].copy() #Otros igual a ...
    data_9_o = data_o[~data_o["motivo"].isin(["Reposición de tiempo", "Horas Extra", "Horas Extra Apoyo Otros Proyectos", "Horas Extras"])].copy() #Otros menos ...

    def agrupar_o_vacio(df, group_cols, agg_col, rename_dict):
        if len(df) > 0:
            res = df.groupby(group_cols, as_index=False)[[agg_col]].agg(np.sum)
            res.rename(columns=rename_dict, inplace=True)
            return res
        else:
            return pd.DataFrame(columns=group_cols + list(rename_dict.values()))

    #Columnas de Resumen Horas, cada una llama la función agrupar_o_vacio quien toma los datos de ej: data_8_r y si hay valores, los agrupa por fecha, nombre y horas.
    #este proceso se repite para todas las demas columnas que llaman la funcion
    prod_normal = agrupar_o_vacio(data_8_r, ["nombre", "fecha"], "horas", {"horas": "horas_produccion"})
    prod_extra = agrupar_o_vacio(data_6_r, ["nombre", "fecha"], "horas", {"horas": "horas_extra_produccion"})
    cap = agrupar_o_vacio(data_c, ["nombre", "fecha"], "horas", {"horas": "horas_capacitacion"})
    otros = agrupar_o_vacio(data_9_o, ["nombre", "fecha"], "horas", {"horas": "horas_otros_registros"})
    otros_extra = agrupar_o_vacio(data_6_o, ["nombre", "fecha"], "horas", {"horas": "horas_extra_otros_registros"})
    reposicion = agrupar_o_vacio(data_7_o, ["nombre", "fecha"], "horas", {"horas": "reposicion"})

    datos_horas = pd.concat([prod_normal, prod_extra, cap, otros, otros_extra], axis=0)
    if len(datos_horas) == 0:
        return pd.DataFrame()

    keys = datos_horas[["nombre", "fecha"]].drop_duplicates() #Se crean PK unicos nombre+fecha ej: BrandonMataOrtega2026-03-01
    merged = keys.merge(prod_normal, on=["nombre", "fecha"], how="left") #busca desde prod_normal coincidencias para meter en la columna de "BrandonMataOrtega2026-03-01 el valor de horas, si no hay asigna un "NaN" equivalente a "null"
    merged = merged.merge(prod_extra, on=["nombre", "fecha"], how="left")
    merged = merged.merge(cap, on=["nombre", "fecha"], how="left")
    merged = merged.merge(otros, on=["nombre", "fecha"], how="left")
    merged = merged.merge(otros_extra, on=["nombre", "fecha"], how="left")
    merged = merged.merge(reposicion, on=["nombre", "fecha"], how="left")
    merged = merged.fillna(0)#reemplazamos los "NaN" a 0

    cols_numeric = ["horas_produccion", "horas_extra_produccion", "horas_capacitacion",
                    "horas_otros_registros", "horas_extra_otros_registros", "reposicion"]
    for col in cols_numeric:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)

    merged["Total"] = merged["horas_produccion"] + merged["horas_capacitacion"] + merged["horas_otros_registros"]
    return merged


def generar_resumen_produccion(data_r, modo_supervisor=False):
    if len(data_r) == 0:
        return pd.DataFrame(), pd.DataFrame()

    diario = data_r.groupby(["nombre", "fecha"], as_index=False)[["lotes", "edificas", "horas"]].agg(np.sum)
    diario["rendimiento"] = (diario["edificas"] / diario["horas"]) * 8.5

    semanal = data_r.groupby(["nombre", "semana", "proceso"], as_index=False)[["edificas", "unidades_catastrales", "horas"]].agg(np.sum)

    if modo_supervisor:
        # Lógica antigua para Supervisor/Coordinador
        valor_esperado_map = {
            'Precampo': 340,
            'Control de Calidad Precampo': 510,
            'Postcampo': 340,
            'Control de Calidad Postcampo': 765
        }
        semanal["valor esperado"] = semanal["proceso"].map(valor_esperado_map).fillna(0)
        semanal["diferencia"] = semanal["edificas"] - semanal["valor esperado"]
    else:
        # Lógica nueva para Operario/Profesional Jurídico
        tasa_por_hora = {
            'Precampo': 8,
            'Control de Calidad Precampo': 10,
            'Postcampo': 7,
            'Control de Calidad Postcampo': 10,
            'Vinculación Precampo': 8,
            'Control de Calidad Vinculación Precampo': 10
        }
        semanal["valor esperado"] = semanal["proceso"].map(tasa_por_hora).fillna(0) * semanal["horas"]
        semanal["diferencia"] = semanal["edificas"] + semanal["unidades_catastrales"] - semanal["valor esperado"]
        semanal["ratio bruto"] = (semanal["edificas"] + semanal["unidades_catastrales"]) / semanal["horas"]

    return diario, semanal

def generar_resumen_calidad(data_r):
    if len(data_r) == 0:
        return pd.DataFrame()

    data_filtrada = data_r[(data_r["tipo"] == "Inspección") & (data_r["operador_cc"].notna()) & (data_r["operador_cc"] != "N/A")]
    if len(data_filtrada) == 0:
        return pd.DataFrame()

    resumen = data_filtrada.groupby(["operador_cc", "semana"], as_index=False)[["edificas", "aprobados", "rechazados"]].agg(np.sum)
    resumen["porcentaje_aprobacion"] = ((resumen["aprobados"] / resumen["edificas"]) * 100).round(2).astype(str) + "%"
    return resumen


def generar_resumen_calidad_operario(data_5_r):
    if len(data_5_r) == 0:
        return pd.DataFrame()

    data_filtrada = data_5_r[data_5_r["tipo"] == "Inspección"]
    if len(data_filtrada) == 0:
        return pd.DataFrame()

    resumen = data_filtrada.groupby(["operador_cc", "semana"], as_index=False)[["edificas", "unidades_catastrales", "aprobados", "rechazados"]].agg(np.sum)
    resumen["porcentaje_aprobacion"] = ((resumen["aprobados"] / (resumen["edificas"] + resumen["unidades_catastrales"])) * 100).round(2).astype(str) + "%"
    return resumen


# -------------------------------------------------------------------
# FUNCIONES DE VISUALIZACIÓN (Placeholders)
# -------------------------------------------------------------------

def limpiar_placeholders(lista_placeholders):
    for ph in lista_placeholders:
        if ph is not None:
            ph.empty()


def mostrar_reporte_base(data, placeholder):
    if len(data) == 0:
        placeholder.error("No existen reportes para mostrar")
    else:
        placeholder.dataframe(data)


def mostrar_resumen_horas(datos_horas, placeholder_tabla, placeholder_error):
    if len(datos_horas) == 0:
        placeholder_error.error("No existen horas para mostrar")
    else:
        placeholder_tabla.dataframe(datos_horas)


def mostrar_resumen_produccion(diario, semanal, data_r, placeholder_diario, placeholder_semanal_titulo,
                               placeholder_semanal, placeholder_error):
    if len(data_r) == 0:
        placeholder_error.error("No existe producción para mostrar")
        return

    placeholder_diario.dataframe(diario)
    placeholder_semanal_titulo.subheader("Resumen Semanal")
    placeholder_semanal.dataframe(semanal)


# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL Historial
# -------------------------------------------------------------------

def Historial(usuario, puesto):
    nombre_df = fetch_df("SELECT nombre FROM usuarios WHERE usuario = %s", params=[usuario])
    nombre_7 = nombre_df.loc[0, 'nombre'] if not nombre_df.empty else ""

    default_date = datetime.now(pytz.timezone('America/Guatemala'))

    # --- Sidebar ---
    ph_sidebar = []
    ph_titulo = st.sidebar.empty()
    ph_titulo.title("Menú")
    ph_sidebar.append(ph_titulo)

    btn_procesos = st.sidebar.empty()
    ph_sidebar.append(btn_procesos)
    btn_capacitacion = st.sidebar.empty()
    ph_sidebar.append(btn_capacitacion)
    btn_otros = st.sidebar.empty()
    ph_sidebar.append(btn_otros)
    btn_bonos = st.sidebar.empty()
    ph_sidebar.append(btn_bonos)
    btn_salir = st.sidebar.empty()
    ph_sidebar.append(btn_salir)

    # --- Contenido principal ---
    ph_main = []
    titulo_historial = st.empty()
    ph_main.append(titulo_historial)
    titulo_historial.title("Historial")

    fecha_inicio = st.empty()
    ph_main.append(fecha_inicio)
    fecha_fin = st.empty()
    ph_main.append(fecha_fin)

    fecha_inicio_val = fecha_inicio.date_input("Fecha de Inicio", value=default_date, key="fecha_inicio")
    fecha_fin_val = fecha_fin.date_input("Fecha de Finalización", value=default_date, key="fecha_fin")

    placeholders_contenido = []

    # Filtros según perfil
    if puesto in ["Supervisor", "Técnico SIG", "Coordinador"]:
        filtro_personal = st.empty()
        placeholders_contenido.append(filtro_personal)
        filtro_proceso = st.empty()
        placeholders_contenido.append(filtro_proceso)
        filtro_tipo = st.empty()
        placeholders_contenido.append(filtro_tipo)

        personal_sel = filtro_personal.selectbox("Personal", options=("Todos", "Operarios", "Profesional Jurídico", "Propio", "Personal Asignado"), key="filtro_personal")
        proceso_sel = filtro_proceso.selectbox("Proceso", options=("Todos","Postcampo Folios de Matricula Inmobiliaria","Postcampo Control de Calidad FMI","Control de Calidad Folios de Matricula Inmobiliaria","Calidad Externa XTF","Consultas de Campo","Folios de Matricula Inmobiliaria","Precampo","Control de Calidad Precampo","Preparación de Insumos","Entregas Postcampo","Postcampo","Control de Calidad Postcampo","Restitución de Tierras","Revisión de Predios Segregados","Vinculación Precampo","Control de Calidad Vinculación Precampo"), key="proceso_sup")
        tipo_sel = filtro_tipo.selectbox("Tipo", options=("Todos","Ordinario","Corrección","Corrección Inspección","Corrección Primera Reinspección","Reproceso Ordinario","Reproceso Corrección Inspección","Reproceso Corrección Primera Reinspección","Inspección","Reinspección","Primera Reinspección","Segunda Reinspección","Reproceso Inspección","Reproceso Primera Reinspección","Reproceso Segunda Reinspección"), key="tipo_sup")

        data_r, data_c, data_o = cargar_datos_supervisor(fecha_inicio_val, fecha_fin_val, personal_sel, proceso_sel, tipo_sel, nombre_7)
    else:
        filtro_proceso_op = st.empty()
        placeholders_contenido.append(filtro_proceso_op)
        filtro_tipo_op = st.empty()
        placeholders_contenido.append(filtro_tipo_op)

        proceso_sel = filtro_proceso_op.selectbox("Proceso", options=("Todos","Control de Calidad Folios de Matricula Inmobiliaria","Postcampo Control de Calidad FMI","Consultas de Campo","Postcampo Folios de Matricula Inmobiliaria","Folios de Matricula Inmobiliaria","Precampo", "Control de Calidad Precampo","Preparación de Insumos","Entregas Postcampo","Postcampo","Control de Calidad Postcampo","Restitución de Tierras","Revisión de Predios Segregados","Vinculación Precampo","Control de Calidad Vinculación Precampo"), key="proceso_op")
        tipo_sel = filtro_tipo_op.selectbox("Tipo", options=("Todos","Ordinario","Corrección","Corrección Inspección","Correccion Primera Reinspección","Inspección","Reinspección","Primera Reinspección","Segunda Reinspección","Reproceso Inspección","Reproceso Primera Reinspección"), key="tipo_op")

        data_1_r, data_8_r, data_6_r, data_5_r, data_1_c, data_1_o, data_6_o, data_9_o, data_7_o = cargar_datos_operario(
            usuario, fecha_inicio_val, fecha_fin_val, proceso_sel, tipo_sel, nombre_7
        )
        data_r = data_1_r
        data_c = data_1_c
        data_o = data_1_o

    # --- Placeholders para secciones de resultados (orden correcto) ---
    ph_reporte_titulo = st.empty()
    placeholders_contenido.append(ph_reporte_titulo)
    ph_reporte_data = st.empty()
    placeholders_contenido.append(ph_reporte_data)

    ph_horas_titulo = st.empty()
    placeholders_contenido.append(ph_horas_titulo)
    ph_horas_data = st.empty()
    placeholders_contenido.append(ph_horas_data)
    ph_horas_error = st.empty()
    placeholders_contenido.append(ph_horas_error)

    ph_prod_titulo = st.empty()
    placeholders_contenido.append(ph_prod_titulo)
    ph_prod_diario = st.empty()
    placeholders_contenido.append(ph_prod_diario)
    ph_prod_semanal_titulo = st.empty()
    placeholders_contenido.append(ph_prod_semanal_titulo)
    ph_prod_semanal = st.empty()
    placeholders_contenido.append(ph_prod_semanal)
    ph_prod_error = st.empty()
    placeholders_contenido.append(ph_prod_error)

    # Calidad
    if puesto in ["Supervisor", "Técnico SIG", "Coordinador"]:
        ph_calidad_titulo = st.empty()
        placeholders_contenido.append(ph_calidad_titulo)
        ph_calidad_data = st.empty()
        placeholders_contenido.append(ph_calidad_data)
    else:
        ph_calidad_titulo_op = st.empty()
        placeholders_contenido.append(ph_calidad_titulo_op)
        ph_calidad_data_op = st.empty()
        placeholders_contenido.append(ph_calidad_data_op)

    # --- Procesamiento y visualización ---
    ph_reporte_titulo.subheader("Reportes")
    mostrar_reporte_base(data_r, ph_reporte_data)

    ph_horas_titulo.subheader("Resumen de Horas")
    if puesto in ["Supervisor", "Técnico SIG", "Coordinador"]:
        datos_horas = generar_resumen_horas(data_r, data_c, data_o)
    else:
        def generar_horas_operario():
            prod_normal = data_8_r.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "horas_produccion"}) if len(data_8_r) > 0 else pd.DataFrame(columns=["nombre","fecha","horas_produccion"])
            prod_extra = data_6_r.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "horas_extra_produccion"}) if len(data_6_r) > 0 else pd.DataFrame(columns=["nombre","fecha","horas_extra_produccion"])
            cap = data_1_c.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "horas_capacitacion"}) if len(data_1_c) > 0 else pd.DataFrame(columns=["nombre","fecha","horas_capacitacion"])
            otros = data_9_o.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "horas_otros_registros"}) if len(data_9_o) > 0 else pd.DataFrame(columns=["nombre","fecha","horas_otros_registros"])
            otros_extra = data_6_o.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "horas_extra_otros_registros"}) if len(data_6_o) > 0 else pd.DataFrame(columns=["nombre","fecha","horas_extra_otros_registros"])
            reposicion = data_7_o.groupby(["nombre", "fecha"], as_index=False)["horas"].agg(np.sum).rename(columns={"horas": "reposicion"}) if len(data_7_o) > 0 else pd.DataFrame(columns=["nombre","fecha","reposicion"])

            combined = pd.concat([prod_normal, prod_extra, cap, otros, otros_extra], axis=0)
            if len(combined) == 0:
                return pd.DataFrame()
            keys = combined[["nombre","fecha"]].drop_duplicates()
            merged = keys.merge(prod_normal, on=["nombre","fecha"], how="left").merge(prod_extra, on=["nombre","fecha"], how="left").merge(cap, on=["nombre","fecha"], how="left").merge(otros, on=["nombre","fecha"], how="left").merge(otros_extra, on=["nombre","fecha"], how="left").merge(reposicion, on=["nombre","fecha"], how="left").fillna(0)
            for col in ["horas_produccion","horas_capacitacion","horas_otros_registros"]:
                if col in merged.columns:
                    merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0)
            merged["Total"] = merged["horas_produccion"] + merged["horas_capacitacion"] + merged["horas_otros_registros"]
            return merged

        datos_horas = generar_horas_operario()

    mostrar_resumen_horas(datos_horas, ph_horas_data, ph_horas_error)


    # --- Resumen de Producción ---
    ph_prod_titulo.subheader("Resumen de Producción")
    
    if puesto in ["Supervisor", "Técnico SIG", "Coordinador"]:
        diario, semanal = generar_resumen_produccion(data_r, modo_supervisor=True)
        mostrar_resumen_produccion(diario, semanal, data_r, ph_prod_diario, ph_prod_semanal_titulo,
                                   ph_prod_semanal, ph_prod_error)
    else:
        diario, semanal = generar_resumen_produccion(data_r, modo_supervisor=False)
        if len(data_r) == 0:
            ph_prod_error.error("No existe producción para mostrar")
        else:
            # Para operario: no mostrar tabla diaria, solo la semanal con título específico
            ph_prod_semanal_titulo.subheader("Resumen de Producción por Proceso")
            ph_prod_semanal.dataframe(semanal)

        # Resumen de Calidad
    if puesto in ["Supervisor", "Técnico SIG", "Coordinador"]:
        ph_calidad_titulo.subheader("Resumen Calidad")
        calidad = generar_resumen_calidad(data_r)
        if len(calidad) == 0:
            ph_calidad_data.error("No existen reportes para mostrar")  # ✅ Usar el placeholder existente
        else:
            calidad_vista = calidad.rename(columns={"edificas": "muestra"})
            ph_calidad_data.dataframe(calidad_vista)
    else:
        ph_calidad_titulo_op.subheader("Resumen Calidad")
        calidad_op = generar_resumen_calidad_operario(data_5_r)
        if len(calidad_op) == 0:
            ph_calidad_data_op.error("No existen reportes para mostrar")  # ✅ Usar el placeholder existente
        else:
            calidad_vista = calidad_op.rename(columns={"unidades_catastrales": "muestra unidades catastrales", "edificas": "muestra edificas"})
            ph_calidad_data_op.dataframe(calidad_vista)
    # --- Navegación ---
    if btn_procesos.button("Procesos", key="procesos_hist"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        perfil_df = fetch_df("SELECT perfil FROM usuarios WHERE usuario = %s", params=[usuario])
        perfil = str(perfil_df.loc[0, 'perfil']) if not perfil_df.empty else "1"
        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        else:
            Procesos.Procesos3(usuario, puesto)

    elif btn_capacitacion.button("Capacitaciones", key="capacitacion_hist"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif btn_otros.button("Otros Registros", key="otros_hist"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif btn_bonos.button("Bonos y Horas Extras", key="bonos_hist"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif btn_salir.button("Salir", key="salir_hist"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Ingreso = False
        st.session_state.Historial = False
        st.session_state.Salir = True
        Salir.Salir()
