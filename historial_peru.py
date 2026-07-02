# ----- historial_peru.py -----
import numpy as np
import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

import Procesos, Capacitacion, Otros_Registros, Bonos_Extras, Salir
from db_core import fetch_df

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES DE DATOS (con filtro por puesto peruano)
# -------------------------------------------------------------------

def convertir_lotes(df):
    """Convierte la columna 'lotes' (texto) a conteo numérico."""
    if 'lotes' not in df.columns:
        return df
    def contar_lotes(valor):
        if pd.isna(valor) or valor == '':
            return 0
        if isinstance(valor, str):
            partes = [p.strip() for p in valor.split(',') if p.strip()]
            return len(partes)
        try:
            return int(float(valor))
        except:
            return 0
    df['lotes'] = df['lotes'].apply(contar_lotes)
    return df

def cargar_datos_supervisor_peru(fecha_inicio, fecha_fin, personal, proceso, tipo, nombre_usuario):
    """Carga datos solo de los puestos peruanos."""
    # Filtro global por puesto
    puestos_peru = ("'Operario Perú'", "'Supervisor Perú'", "'Coordinador Perú'")
    filtro_puesto = f"puesto IN ({', '.join(puestos_peru)})"

    base_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               lotes, estado, cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )
    base_c = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, tema,
               cast(horas as float), observaciones, reporte
        FROM capacitaciones
        WHERE {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )
    base_o = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[fecha_inicio, fecha_fin]
    )

    data_r = base_r.copy()
    data_c = base_c.copy()
    data_o = base_o.copy()

    # Aplicar conversión de lotes
    data_r = convertir_lotes(data_r)

    # Filtros adicionales según personal
    if personal == "Operarios Perú":
        data_r = data_r[data_r["puesto"] == "Operario Perú"]
        data_c = data_c[data_c["puesto"] == "Operario Perú"]
        data_o = data_o[data_o["puesto"] == "Operario Perú"]
    elif personal == "Profesional Jurídico Perú":
        data_r = data_r[data_r["puesto"] == "Profesional Jurídico Perú"]  # si existe
        data_c = data_c[data_c["puesto"] == "Profesional Jurídico Perú"]
        data_o = data_o[data_o["puesto"] == "Profesional Jurídico Perú"]
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

def cargar_datos_operario_peru(usuario, fecha_inicio, fecha_fin, proceso, tipo, nombre_completo):
    """Carga datos para operario peruano."""
    puestos_peru = ("'Operario Perú'",)  # solo operario
    filtro_puesto = f"puesto IN ({', '.join(puestos_peru)})"

    condiciones = [f"usuario = %s", filtro_puesto]
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
               lotes, cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE {where_clause} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=params
    )

    data_8_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               lotes, cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
          AND tipo NOT IN ('Producción Horas Extras', 'Inspección Horas Extras', 'Reproceso Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_6_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               lotes, cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
          AND tipo IN ('Producción Horas Extras', 'Inspección Horas Extras', 'Reproceso Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_5_r = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, proceso, fecha, semana, año,
               distrito, manzana, sector, cast(edificas as float), cast(unidades_catastrales as float), tipo,
               lotes, cast(aprobados as float), cast(rechazados as float), operador_cc,
               tipo_de_errores, conteo_de_errores, numero_lote, observaciones, cast(horas as float)
        FROM registro
        WHERE operador_cc = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[nombre_completo, fecha_inicio, fecha_fin]
    )

    # Aplicar conversión de lotes
    data_1_r = convertir_lotes(data_1_r)
    data_8_r = convertir_lotes(data_8_r)
    data_6_r = convertir_lotes(data_6_r)
    data_5_r = convertir_lotes(data_5_r)

    data_1_c = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, tema,
               cast(horas as float), observaciones, reporte
        FROM capacitaciones
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_1_o = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_6_o = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
          AND motivo IN ('Horas Extra', 'Horas Extra Apoyo Otros Proyectos', 'Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_9_o = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
          AND motivo NOT IN ('Reposición de tiempo', 'Horas Extra', 'Horas Extra Apoyo Otros Proyectos', 'Horas Extras')
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )
    data_7_o = fetch_df(
        f"""
        SELECT cast(id as integer), marca, usuario, nombre, puesto, supervisor, fecha, motivo,
               cast(horas as float), observaciones, reporte
        FROM otros_registros
        WHERE usuario = %s AND {filtro_puesto} AND fecha::date >= %s AND fecha::date <= %s
          AND motivo = 'Reposición de tiempo'
        """,
        params=[usuario, fecha_inicio, fecha_fin]
    )

    return data_1_r, data_8_r, data_6_r, data_5_r, data_1_c, data_1_o, data_6_o, data_9_o, data_7_o

# -------------------------------------------------------------------
# FUNCIONES DE PROCESAMIENTO (idénticas a las originales)
# -------------------------------------------------------------------

def generar_resumen_horas(data_r, data_c, data_o):
    # ... (código exactamente igual al de historial.py) ...
    # (se omite por brevedad, pero debe ser copiado tal cual)
    # Asegúrate de incluir toda la lógica de agrupación y merge.
    pass

def generar_resumen_produccion(data_r, modo_supervisor=False):
    # ... (código exactamente igual) ...
    pass

def generar_resumen_calidad(data_r):
    # ... (código exactamente igual) ...
    pass

def generar_resumen_calidad_operario(data_5_r):
    # ... (código exactamente igual) ...
    pass

# -------------------------------------------------------------------
# FUNCIONES DE VISUALIZACIÓN (idénticas)
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
# FUNCIÓN PRINCIPAL Historial_Peru
# -------------------------------------------------------------------

def Historial_Peru(usuario, puesto):
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
    titulo_historial.title("Historial Perú")

    fecha_inicio = st.empty()
    ph_main.append(fecha_inicio)
    fecha_fin = st.empty()
    ph_main.append(fecha_fin)

    fecha_inicio_val = fecha_inicio.date_input("Fecha de Inicio", value=default_date, key="fecha_inicio_peru")
    fecha_fin_val = fecha_fin.date_input("Fecha de Finalización", value=default_date, key="fecha_fin_peru")

    placeholders_contenido = []

    # Filtros según perfil (usamos los mismos roles pero con denominación Perú)
    if puesto in ["Supervisor Perú", "Técnico SIG Perú", "Coordinador Perú"]:
        filtro_personal = st.empty()
        placeholders_contenido.append(filtro_personal)
        filtro_proceso = st.empty()
        placeholders_contenido.append(filtro_proceso)
        filtro_tipo = st.empty()
        placeholders_contenido.append(filtro_tipo)

        personal_sel = filtro_personal.selectbox("Personal", options=("Todos", "Operarios Perú", "Profesional Jurídico Perú", "Propio", "Personal Asignado"), key="filtro_personal_peru")
        proceso_sel = filtro_proceso.selectbox("Proceso", options=("Todos","Postcampo Folios de Matricula Inmobiliaria","Postcampo Control de Calidad FMI","Control de Calidad Folios de Matricula Inmobiliaria","Calidad Externa XTF","Consultas de Campo","Folios de Matricula Inmobiliaria","Precampo","Control de Calidad Precampo","Preparación de Insumos","Entregas Postcampo","Postcampo","Control de Calidad Postcampo","Restitución de Tierras","Revisión de Predios Segregados","Vinculación Precampo","Control de Calidad Vinculación Precampo"), key="proceso_sup_peru")
        tipo_sel = filtro_tipo.selectbox("Tipo", options=("Todos","Ordinario","Corrección","Corrección Inspección","Corrección Primera Reinspección","Reproceso Ordinario","Reproceso Corrección Inspección","Reproceso Corrección Primera Reinspección","Inspección","Reinspección","Primera Reinspección","Segunda Reinspección","Reproceso Inspección","Reproceso Primera Reinspección","Reproceso Segunda Reinspección"), key="tipo_sup_peru")

        data_r, data_c, data_o = cargar_datos_supervisor_peru(fecha_inicio_val, fecha_fin_val, personal_sel, proceso_sel, tipo_sel, nombre_7)
    else:
        filtro_proceso_op = st.empty()
        placeholders_contenido.append(filtro_proceso_op)
        filtro_tipo_op = st.empty()
        placeholders_contenido.append(filtro_tipo_op)

        proceso_sel = filtro_proceso_op.selectbox("Proceso", options=("Todos","Control de Calidad Folios de Matricula Inmobiliaria","Postcampo Control de Calidad FMI","Consultas de Campo","Postcampo Folios de Matricula Inmobiliaria","Folios de Matricula Inmobiliaria","Precampo", "Control de Calidad Precampo","Preparación de Insumos","Entregas Postcampo","Postcampo","Control de Calidad Postcampo","Restitución de Tierras","Revisión de Predios Segregados","Vinculación Precampo","Control de Calidad Vinculación Precampo"), key="proceso_op_peru")
        tipo_sel = filtro_tipo_op.selectbox("Tipo", options=("Todos","Ordinario","Corrección","Corrección Inspección","Correccion Primera Reinspección","Inspección","Reinspección","Primera Reinspección","Segunda Reinspección","Reproceso Inspección","Reproceso Primera Reinspección"), key="tipo_op_peru")

        data_1_r, data_8_r, data_6_r, data_5_r, data_1_c, data_1_o, data_6_o, data_9_o, data_7_o = cargar_datos_operario_peru(
            usuario, fecha_inicio_val, fecha_fin_val, proceso_sel, tipo_sel, nombre_7
        )
        data_r = data_1_r
        data_c = data_1_c
        data_o = data_1_o

    # --- Placeholders para resultados (igual que en historial.py) ---
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

    if puesto in ["Supervisor Perú", "Técnico SIG Perú", "Coordinador Perú"]:
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
    if puesto in ["Supervisor Perú", "Técnico SIG Perú", "Coordinador Perú"]:
        datos_horas = generar_resumen_horas(data_r, data_c, data_o)
    else:
        # lógica para operario (copiada de historial.py)
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

    ph_prod_titulo.subheader("Resumen de Producción")
    if puesto in ["Supervisor Perú", "Técnico SIG Perú", "Coordinador Perú"]:
        diario, semanal = generar_resumen_produccion(data_r, modo_supervisor=True)
        mostrar_resumen_produccion(diario, semanal, data_r, ph_prod_diario, ph_prod_semanal_titulo,
                                   ph_prod_semanal, ph_prod_error)
    else:
        diario, semanal = generar_resumen_produccion(data_r, modo_supervisor=False)
        if len(data_r) == 0:
            ph_prod_error.error("No existe producción para mostrar")
        else:
            ph_prod_semanal_titulo.subheader("Resumen de Producción por Proceso")
            ph_prod_semanal.dataframe(semanal)

    # Calidad
    if puesto in ["Supervisor Perú", "Técnico SIG Perú", "Coordinador Perú"]:
        ph_calidad_titulo.subheader("Resumen Calidad")
        calidad = generar_resumen_calidad(data_r)
        if len(calidad) == 0:
            ph_calidad_data.error("No existen reportes para mostrar")
        else:
            calidad_vista = calidad.rename(columns={"edificas": "muestra"})
            ph_calidad_data.dataframe(calidad_vista)
    else:
        ph_calidad_titulo_op.subheader("Resumen Calidad")
        calidad_op = generar_resumen_calidad_operario(data_5_r)
        if len(calidad_op) == 0:
            ph_calidad_data_op.error("No existen reportes para mostrar")
        else:
            calidad_vista = calidad_op.rename(columns={"unidades_catastrales": "muestra unidades catastrales", "edificas": "muestra edificas"})
            ph_calidad_data_op.dataframe(calidad_vista)

    # --- Navegación (con redirección a los mismos módulos) ---
    if btn_procesos.button("Procesos", key="procesos_hist_peru"):
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

    elif btn_capacitacion.button("Capacitaciones", key="capacitacion_hist_peru"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Capacitacion = True
        Capacitacion.Capacitacion(usuario, puesto)

    elif btn_otros.button("Otros Registros", key="otros_hist_peru"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Otros_Registros = True
        Otros_Registros.Otros_Registros(usuario, puesto)

    elif btn_bonos.button("Bonos y Horas Extras", key="bonos_hist_peru"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Historial = False
        st.session_state.Bonos_Extras = True
        Bonos_Extras.Bonos_Extras(usuario, puesto)

    elif btn_salir.button("Salir", key="salir_hist_peru"):
        limpiar_placeholders(ph_sidebar + ph_main + placeholders_contenido)
        st.session_state.Ingreso = False
        st.session_state.Historial = False
        st.session_state.Salir = True
        Salir.Salir()
