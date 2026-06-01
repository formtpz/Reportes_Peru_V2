# ----- Librerías -----
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import Procesos
from db_core import fetch_df, fetch_one, execute


def Correcciones(usuario, puesto):

    # =============================
    # Utilidad numpy → python (por si acaso)
    # =============================
    def to_python(v):
        return v.item() if hasattr(v, "item") else v

    # =============================
    # Función auxiliar para convertir cualquier valor a date
    # =============================
    def _a_date(valor):
        if valor is None:
            return None
        if isinstance(valor, str):
            # Intentar formatos comunes
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    return datetime.strptime(valor, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"No se pudo convertir '{valor}' a fecha")
        if hasattr(valor, 'date'):
            return valor.date()
        # Asumir que ya es date
        return valor

    # =============================
    # Menú lateral
    # =============================
    placeholder1_3 = st.sidebar.empty()
    placeholder1_3.title("Menú")
    placeholder2_3 = st.sidebar.empty()
    procesos_3 = placeholder2_3.button("Regresar", key="procesos_3")

    # =========================================================
    # USUARIO NORMAL (NO COORDINADOR)
    # =========================================================
    if puesto != "Coordinador":

        page = st.empty()
        with page.container():

            st.title("Solicitud de Corrección de Reportes")
            st.write("Aquí puedes visualizar tus reportes recientes y solicitar correcciones o eliminaciones.")
            st.subheader("🎥 Material de apoyo")
            st.markdown(
                """
                - **Sin VPN:** [Video de Capacitación](http://wiki.tpzcr.com:8060/doku.php?id=app_reportes_-streamlit)  
                - **Con VPN:** [Video de Capacitación](http://wiki.tpzcr.com/doku.php?id=app_reportes_-streamlit)
                """
            )

            # -------------------------------------------------
            # Obtener nombre del usuario
            # -------------------------------------------------
            df_nombre = fetch_df(
                "SELECT nombre FROM usuarios WHERE usuario = %s",
                params=(usuario,)
            )
            nombre = df_nombre.loc[0, "nombre"] if not df_nombre.empty else ""

            # -------------------------------------------------
            # Filtro fijo: últimos 3 días
            # -------------------------------------------------
            fecha_limite = datetime.now().date() - timedelta(days=3)

            # -- Registro (se filtra por usuario) --
            query_registro = """
                SELECT *
                FROM registro
                WHERE usuario = %s AND fecha::date >= %s
                ORDER BY fecha DESC
            """
            df_registro = fetch_df(query_registro, params=(usuario, fecha_limite))

            # -- Otros registros (se filtra por reporte = nombre) --
            query_otros = """
                SELECT *
                FROM otros_registros
                WHERE reporte = %s AND fecha::date >= %s
                ORDER BY fecha DESC
            """
            df_otros = fetch_df(query_otros, params=(nombre, fecha_limite))

            # -- Capacitaciones (se filtra por reporte = nombre) --
            query_capacitacion = """
                SELECT *
                FROM capacitaciones
                WHERE reporte = %s AND fecha::date >= %s
                ORDER BY fecha DESC
            """
            df_capacitaciones = fetch_df(query_capacitacion, params=(nombre, fecha_limite))

            for df in (df_registro, df_otros, df_capacitaciones):
                if not df.empty and "id" in df.columns:
                    df["id"] = df["id"].astype(str)

            # ---------- Filtro para mostrar una sola tabla ----------
            st.subheader("📋Paso 1) Visualizar reportes recientes (últimos 3 días) y copiar ID a corregir")
            tabla_viz = st.radio(
                "Selecciona la tabla que deseas visualizar:",
                ("Registro", "Otros Registros", "Capacitaciones"),
                horizontal=True
            )
            if tabla_viz == "Registro":
                st.dataframe(df_registro, use_container_width=True)
            elif tabla_viz == "Otros Registros":
                st.dataframe(df_otros, use_container_width=True)
            else:
                st.dataframe(df_capacitaciones, use_container_width=True)

            # ---------- Nueva solicitud de corrección ----------
            st.subheader("➕ Paso 2) Agregar solicitud de Modificación / Eliminación de reporte")

            with st.form(key="nueva_correccion_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    tabla = st.selectbox(
                        "Tabla donde se encuentra el reporte",
                        ("registro", "otros_registros", "capacitaciones")
                    )
                with col2:
                    id_reporte = st.text_input("ID del reporte (copiado de la tabla anterior)")

                tipo_solicitud = st.radio(
                    "Tipo de solicitud",
                    ("Eliminar reporte", "Modificar reporte")
                )
                enviar = st.form_submit_button("Registrar solicitud")

                if enviar:
                    if not id_reporte:
                        st.error("Debe indicar el ID del reporte.")
                    else:
                        # Verificar que el ID exista y pertenezca al usuario
                        if tabla == "registro":
                            registro_info = fetch_one(
                                "SELECT usuario, fecha FROM registro WHERE id = %s",
                                params=(id_reporte,)
                            )
                            if registro_info is None:
                                st.error(f"No existe el ID {id_reporte} en la tabla registro.")
                            elif registro_info["usuario"] != usuario:
                                st.error("No puedes solicitar corrección de un reporte que no te pertenece.")
                            else:
                                pertenece = True
                        else:  # otros_registros o capacitaciones -> usan reporte = nombre
                            registro_info = fetch_one(
                                f"SELECT reporte, fecha FROM {tabla} WHERE id = %s",
                                params=(id_reporte,)
                            )
                            if registro_info is None:
                                st.error(f"No existe el ID {id_reporte} en la tabla {tabla}.")
                            elif registro_info["reporte"] != nombre:
                                st.error("No puedes solicitar corrección de un reporte que no está a tu nombre.")
                            else:
                                pertenece = True

                        if 'pertenece' not in locals():
                            pertenece = False

                        if not pertenece:
                            st.stop()

                        # Validar antigüedad máxima de 3 días
                        try:
                            fecha_reporte = _a_date(registro_info["fecha"])
                        except Exception as e:
                            st.error(f"Error al interpretar la fecha del reporte: {e}")
                            st.stop()

                        if fecha_reporte < fecha_limite:
                            st.error(
                                f"No se pueden solicitar correcciones para reportes con más de 3 días de antigüedad. "
                                f"Este reporte es del {fecha_reporte.strftime('%d/%m/%Y')}."
                            )
                            st.stop()

                        # Verificar que no exista ya una solicitud para ese ID
                        existente = fetch_one(
                            "SELECT 1 FROM correcciones WHERE tabla = %s AND id_asociado = %s",
                            params=(tabla, id_reporte)
                        )
                        if existente is not None:
                            st.error("Ya existe una solicitud para este ID en esta tabla. Solo se permite una solicitud por id")
                        else:
                            marca = datetime.now(pytz.timezone("America/Guatemala")).strftime("%Y-%m-%d %H:%M:%S")
                            solucion = "Eliminar" if tipo_solicitud == "Eliminar reporte" else "Modificar"

                            execute(
                                """
                                INSERT INTO correcciones (
                                    usuario, nombre, tipo_error, id_asociado,
                                    fecha, solucion, tabla, columna, nuevo_valor, estado
                                )
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                """,
                                params=(
                                    usuario, nombre, "Pendiente de detalle", id_reporte,
                                    marca, solucion, tabla, "", "", "Pendiente"
                                )
                            )
                            st.success("Solicitud registrada. Ahora puedes continuar con el Paso 3) editar los detalles de la solicitud.")
                            st.rerun()

            # -------------------------------------------------
            # EDICIÓN DE SOLICITUDES PENDIENTES (data_editor nativo)
            # -------------------------------------------------
            st.subheader("✏️Paso 3) Editar detalles de las solicitudes pendientes")

            query_pendientes = """
                SELECT id, fecha, tabla, id_asociado, solucion, columna, nuevo_valor, estado
                FROM correcciones
                WHERE usuario = %s AND estado = 'Pendiente'
                ORDER BY fecha DESC
            """
            df_pendientes = fetch_df(query_pendientes, params=(usuario,))
            if not df_pendientes.empty and "id" in df_pendientes.columns:
                df_pendientes["id"] = df_pendientes["id"].astype(str)

            if df_pendientes.empty:
                st.info("No tienes solicitudes pendientes para editar.")
            else:
                # Definir las columnas editables por tabla
                COLUMNAS_EDITABLES = {
                    "registro": [
                        "fecha", "horas", "observaciones",
                        "distrito", "tipo", "lotes", "aprobados", "rechazados",
                        "manzana", "sector", "numero_lote", "estado",
                        "edificas","unidades_catastrales", "registros", "partida","operador_cc",
                        "total_de_errores", "errores_por_excepcion",
                        "tipo_de_errores", "conteo_de_errores"
                    ],
                    "otros_registros": ["fecha", "horas", "observaciones"],
                    "capacitaciones": ["fecha", "horas", "observaciones"]
                }

                todas_columnas = sorted(set(
                    COLUMNAS_EDITABLES["registro"] +
                    COLUMNAS_EDITABLES["otros_registros"] +
                    COLUMNAS_EDITABLES["capacitaciones"]
                ))

                st.caption("✏️ Paso Opcional) Haz doble clic en 'Solución' para cambiar entre Eliminar/Modificar reporte en caso de equivocación.")
                st.caption("📂 Paso 1) Haz doble clic en 'Columna' y elige de la lista desplegable la columna a modificar. Omitir si eligió Eliminar reporte.")
                st.caption("⚠️ Paso 2) Llena la columna (nuevo valor) para la columna seleccionada. Omitir si se eligió Eliminar reporte.")
                st.info(f"Columnas válidas por tabla:\n\n"
                        f"**Registro**: {', '.join(COLUMNAS_EDITABLES['registro'])}\n\n"
                        f"**Otros Registros**: {', '.join(COLUMNAS_EDITABLES['otros_registros'])}\n\n"
                        f"**Capacitaciones**: {', '.join(COLUMNAS_EDITABLES['capacitaciones'])}")

                column_config = {
                    "id": st.column_config.Column(disabled=True),
                    "fecha": st.column_config.Column(disabled=True),
                    "tabla": st.column_config.Column(disabled=True),
                    "id_asociado": st.column_config.Column(disabled=True),
                    "estado": st.column_config.Column(disabled=True),
                    "solucion": st.column_config.SelectboxColumn(
                        "Solución",
                        options=["Eliminar", "Modificar"],
                        required=True
                    ),
                    "columna": st.column_config.SelectboxColumn(
                        "Columna a modificar",
                        options=todas_columnas,
                        required=False
                    ),
                    "nuevo_valor": st.column_config.TextColumn("Nuevo valor"),
                }

                df_editado = st.data_editor(
                    df_pendientes,
                    use_container_width=True,
                    num_rows="fixed",
                    column_config=column_config,
                    key="editor_pendientes"
                )

                if st.button("💾 Paso 4) Guardar cambios en solicitudes"):
                    cambios = df_editado.compare(df_pendientes)
                    if cambios.empty:
                        st.info("No se detectaron cambios.")
                    else:
                        errores = []
                        for idx in cambios.index.get_level_values(0).unique():
                            fila_nueva = df_editado.loc[idx]
                            fila_original = df_pendientes.loc[idx]

                            # Si la solución es Eliminar, forzamos columna y nuevo_valor vacíos
                            if fila_nueva["solucion"] == "Eliminar":
                                fila_nueva["columna"] = ""
                                fila_nueva["nuevo_valor"] = ""

                            tabla_actual = fila_nueva["tabla"]
                            columna_elegida = fila_nueva["columna"]

                            if fila_nueva["solucion"] == "Modificar" and columna_elegida:
                                if columna_elegida not in COLUMNAS_EDITABLES.get(tabla_actual, []):
                                    errores.append(f"Fila ID {fila_nueva['id']}: La columna '{columna_elegida}' no es editable en la tabla '{tabla_actual}'.")
                                    continue

                            if (fila_nueva["solucion"] == fila_original["solucion"] and
                                fila_nueva["columna"] == fila_original["columna"] and
                                fila_nueva["nuevo_valor"] == fila_original["nuevo_valor"]):
                                continue

                            execute(
                                """
                                UPDATE correcciones
                                SET solucion = %s,
                                    columna = %s,
                                    nuevo_valor = %s
                                WHERE id = %s
                                """,
                                params=(
                                    fila_nueva["solucion"],
                                    fila_nueva["columna"],
                                    fila_nueva["nuevo_valor"],
                                    fila_nueva["id"]
                                )
                            )

                        if errores:
                            for err in errores:
                                st.error(err)
                            st.warning("Corrige los errores antes de guardar.")
                        else:
                            st.success("Cambios guardados correctamente.")
                            st.rerun()

            # -------------------------------------------------
            # 🗑️ ELIMINAR SOLICITUDES PENDIENTES (por error)
            # -------------------------------------------------
            st.subheader("🗑️ Eliminar solicitudes pendientes erróneas")
            query_pend_del = """
                SELECT id, fecha, tabla, id_asociado, solucion
                FROM correcciones
                WHERE usuario = %s AND estado = 'Pendiente'
                ORDER BY fecha DESC
            """
            df_del = fetch_df(query_pend_del, params=(usuario,))
            if df_del.empty:
                st.info("No tienes solicitudes pendientes que eliminar.")
            else:
                if "id" in df_del.columns:
                    df_del["id"] = df_del["id"].astype(str)

                st.caption("Selecciona las solicitudes que deseas eliminar completamente y pulsa el botón.")
                seleccionados = []
                for idx, row in df_del.iterrows():
                    if st.checkbox(f"{row['fecha']} - {row['tabla']} ID {row['id_asociado']} (Solicitud {row['id']})", key=f"del_{row['id']}"):
                        seleccionados.append(row['id'])

                if seleccionados:
                    if st.button("🗑️ Eliminar solicitudes seleccionadas"):
                        for id_sol in seleccionados:
                            execute("DELETE FROM correcciones WHERE id = %s", params=(id_sol,))
                        st.success(f"Se eliminaron {len(seleccionados)} solicitud(es).")
                        st.rerun()
                else:
                    st.info("No has marcado ninguna solicitud para eliminar.")

            # ---------- Ver todas mis solicitudes ----------
            with st.expander("📋Paso 5) Verificar mis solicitudes (Esta es la solicitud hecha)."):
                query_todas = """
                    SELECT id, fecha, tabla, id_asociado, solucion, columna, nuevo_valor, estado
                    FROM correcciones
                    WHERE usuario = %s
                    ORDER BY fecha DESC
                """
                df_todas = fetch_df(query_todas, params=(usuario,))
                if not df_todas.empty and "id" in df_todas.columns:
                    df_todas["id"] = df_todas["id"].astype(str)
                st.dataframe(df_todas, use_container_width=True)

        # Fin del bloque usuario normal

    # =========================================================
    # COORDINADOR
    # =========================================================
    else:

        page = st.empty()
        with page.container():

            st.title("Gestión de Correcciones")

            filtro = st.selectbox("Mostrar", ("Todos", "Pendiente"))

            query_corr = "SELECT * FROM correcciones"
            if filtro == "Pendiente":
                query_corr += " WHERE estado = 'Pendiente'"

            df_corr_original = fetch_df(query_corr)

            if not df_corr_original.empty and "id" in df_corr_original.columns:
                df_corr_original["id"] = df_corr_original["id"].astype(str)

            column_config_coord = {
                "id": st.column_config.Column(disabled=True),
                "usuario": st.column_config.Column(disabled=True),
                "nombre": st.column_config.Column(disabled=True),
                "fecha": st.column_config.Column(disabled=True),
                "tabla": st.column_config.Column(disabled=True),
                "id_asociado": st.column_config.Column(disabled=True),
            }

            df_corr_editado = st.data_editor(
                df_corr_original,
                use_container_width=True,
                num_rows="fixed",
                column_config=column_config_coord
            )

            if st.button("Guardar cambios"):
                cambios = df_corr_editado.compare(df_corr_original)

                if cambios.empty:
                    st.info("No hay cambios para guardar.")
                else:
                    for idx in cambios.index.get_level_values(0).unique():
                        fila_nueva = df_corr_editado.loc[idx]
                        fila_original = df_corr_original.loc[idx]

                        columnas_cambiadas = [
                            col for col in df_corr_original.columns
                            if fila_nueva[col] != fila_original[col]
                        ]
                        columnas_permitidas = [
                            c for c in columnas_cambiadas
                            if c not in ("id", "usuario", "nombre", "fecha", "tabla", "id_asociado")
                        ]
                        if not columnas_permitidas:
                            continue

                        set_clause = ", ".join(f"{col} = %s" for col in columnas_permitidas)
                        valores = [to_python(fila_nueva[col]) for col in columnas_permitidas]
                        id_python = to_python(fila_nueva["id"])

                        sql = f"""
                            UPDATE correcciones
                            SET {set_clause}
                            WHERE id = %s
                        """
                        execute(sql, params=valores + [id_python])

                    st.success("Cambios guardados correctamente")

    # =========================================================
    # Regresar a Procesos
    # =========================================================
    if procesos_3:

        placeholder1_3.empty()
        placeholder2_3.empty()

        try:
            page.empty()
        except:
            pass

        st.session_state.Procesos = False
        st.session_state.Correcciones = False

        # Obtener perfil del usuario
        perfil_info = fetch_one(
            "SELECT perfil FROM usuarios WHERE usuario = %s",
            params=(usuario,)
        )
        perfil = str(perfil_info["perfil"]) if perfil_info else ""

        if perfil == "1":
            Procesos.Procesos1(usuario, puesto)
        elif perfil == "2":
            Procesos.Procesos2(usuario, puesto)
        elif perfil == "3":
            Procesos.Procesos3(usuario, puesto)
