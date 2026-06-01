# ----- Librerías ---- #

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import Procesos,Historial,Capacitacion,Otros_Registros,Bonos_Extras,Salir
from Autenticacion import obtener_usuario_activo
from db_core import execute
from db_core import fetch_operadores_cc

def CC_Precampo_Juridico(usuario,puesto):

  # ----- Conexión, Botones y Memoria ---- #
  uri=st.secrets.db_credentials.URI

 
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
  bonos_extras_3 = placeholder6_3.button("Bonos y Extras",key="bonos_extras_3")

  placeholder7_3 = st.sidebar.empty()
  salir_3 = placeholder7_3.button("Salir",key="salir_3")

  placeholder8_3 = st.empty()
  cc_precampo_juridico_3 = placeholder8_3.title(":orange[Control de Calidad Precampo Jurídico]")

  default_date_3 = datetime.now(pytz.timezone('America/Guatemala'))

  placeholder9_3= st.empty()
  fecha_3= placeholder9_3.date_input("Fecha",value=default_date_3,key="fecha_3")
  
  placeholder10_3= st.empty()
  distrito_3= placeholder10_3.selectbox("Distrito", options=("Chorrillos","San Juan De Miraflores","Villa el Salvador"),key="municipio_3")
  
  placeholder11_3= st.empty()
  manzana_3= placeholder11_3.selectbox("Mazana", options=("001","002","003","004","005","006","007","008","009","010","011","012","013","014","015","016","017","018","019","020","021","022","023","024","025","026","027","028","029","030","031","032","033","034","035","036","037","038","039","040","041","042","043","044","045","046","047","048","049","050","051","052","053","054","055","056","057","058","058","059","060","061","062","063","064","065","066","067","068","069","070","071","072","073","074","075","076","077","078","079","080","081","082","083","084","085","086","087","088","089","090","091","092","093","094","095","096","097","098","099","100","101","102","103","104","105","106","107","108","109","110","111","112","113","114","115","116","117","118","119","120"), key="manzana_3")

  placeholder12_3= st.empty()
  sector_3= placeholder12_3.selectbox("Sector", options=("01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","39","40","41","42","43","44","45","46","47","48","49","50","51","52","53","54","55","56","57","58","59","60","61","62","63","64","65","66","67","68","69","70","71","72","73","74","75","76","77","78","79","80","81","82","83","84","85","86","87","88","89","90","91","92","93","94","95","96","97","98","99","100","101","102","103","104","105","106","107","108","109","110","111","112","113","114","115","116","117","118","119","120"),key="sector_3")

# =========================
  # Generar lista dinámica
  # =========================
  lotes = ["Todos"] + [f"{i:03d}" for i in range(1,249)]
  
  placeholder13_3 = st.empty()
  
  numero_lote_3 = placeholder13_3.multiselect(
      "Número de Lote",
      options=lotes,
      key="numero_lote_3"
  )
  
  # =========================
  # Lógica para "Todos"
  # =========================
  if "Todos" in numero_lote_3:
      numero_lote_3 = ["Todos"]
  
  # =========================
  # Convertir a texto para guardar
  # =========================
  numero_lote_3 = ",".join(numero_lote_3)
  #---------------------------------------------------------------------------------------------------------------------
  # ----- Selector de Operador con datos desde BD ---- #
  
  # Obtener operadores desde la base de datos con los filtros necesarios
  operadores_disponibles = fetch_operadores_cc(
      filtro_proceso='Jurídico',
      filtro_subproceso=['Descarga', 'Análisis'],
      filtro_proceso_anterior='Jurídico',
      filtro_subproceso_anterior=['Descarga', 'Análisis']
  )
  
  # Crear lista de nombres para el selectbox
  if operadores_disponibles:
      opciones_operadores = [op['nombre'] for op in operadores_disponibles]
  else:
      opciones_operadores = ["No hay operadores disponibles"]
  
  placeholder14_3 = st.empty()
  operador_3 = placeholder14_3.selectbox(
      "Operador objeto de CC",
      options=opciones_operadores,
      key="operador_3"
  )
  #----------------------------------------------------------------------------------------------------------------------------------
  placeholder15_3= st.empty()
  tipo_3= placeholder15_3.selectbox("Tipo", options=("Inspección","Primera Reinspección","Inspección Horas Extras","Control de Calidad Supervisión"), key="tipo_3")

  placeholder16_3= st.empty()
  tipo_de_errores_3= placeholder16_3.multiselect("Tipo Errores", options=("Numeración errónea o incompleta","Errores geométricos y/o de forma","Polígonos y/o puntos duplicados","Omisión/Comisión de polígonos","Polígonos no se ajustan a ortofoto","Omisión/Comisión de puertas"), key="tipo_de_errores_3")
    
  placeholderP_3= st.empty()
  partida_3= placeholderP_3.text_input("Número de Partida",value='N/A',max_chars=60,key="partida_3")
  
  placeholder17_3= st.empty()
  aprobados_3= placeholder17_3.number_input("Cantidad de Registros Aprobados",min_value=0,step=1,key="aprobados_3")

  placeholder18_3= st.empty()
  rechazados_3= placeholder18_3.number_input("Cantidad de Registros Rechazados",min_value=0,step=1,key="rechazados_3")
  
  placeholder19_3= st.empty()
  horas_3= placeholder19_3.number_input("Cantidad de Horas Trabajadas en el Proceso",min_value=0.0,key="horas_3")
  
  placeholder20_3 = st.empty()
  reporte_3 = placeholder20_3.button("Generar Reporte",key="reporte_3")

  # ----- Procesos ---- #
    
  if procesos_3:
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.Procesos=False
    st.session_state.CC_Precampo_Juridico=False

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
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.CC_Precampo_Juridico=False
    st.session_state.Historial=True
    Historial.Historial(usuario,puesto)   

  # ----- Capacitación ---- #
    
  elif capacitacion_3:
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.CC_Precampo_Juridico=False
    st.session_state.Capacitacion=True
    Capacitacion.Capacitacion(usuario,puesto)

  # ----- Otros Registros ---- #
    
  elif otros_registros_3:
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.CC_Precampo_Juridico=False
    st.session_state.Otros_Registros=True
    Otros_Registros.Otros_Registros(usuario,puesto)

  # ----- Bonos y Horas Extras ---- #
    
  elif bonos_extras_3:
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.CC_Precampo_Juridico=False
    st.session_state.Bonos_Extras=True
    Bonos_Extras.Bonos_Extras(usuario,puesto)    

    # ----- Salir ---- #
    
  elif salir_3:
    placeholder1_3.empty()
    placeholder2_3.empty()
    placeholder3_3.empty()
    placeholder4_3.empty()
    placeholder5_3.empty()
    placeholder6_3.empty()
    placeholder7_3.empty()
    placeholder8_3.empty()
    placeholder9_3.empty()
    placeholder10_3.empty()
    placeholder11_3.empty()
    placeholder12_3.empty()
    placeholder13_3.empty()
    placeholder14_3.empty()
    placeholder15_3.empty()
    placeholder16_3.empty()
    placeholderP_3.empty()
    placeholder17_3.empty()
    placeholder18_3.empty()
    placeholder19_3.empty()
    placeholder20_3.empty()
    st.session_state.Ingreso = False
    st.session_state.CC_Precampo_Juridico=False
    st.session_state.Salir=True
    Salir.Salir()

  elif reporte_3:

    marca_3= datetime.now(pytz.timezone('America/Bogota')).strftime("%Y-%m-%d %H:%M:%S")
    
    usuario_activo = obtener_usuario_activo(usuario)
    if not usuario_activo:
      st.error("No se encontró un usuario activo para generar el reporte.")
      return

    nombre_3 = usuario_activo["nombre"]
    supervisor_3 = usuario_activo["supervisor"]

    unidades_catastrales_3 = aprobados_3 + rechazados_3

    semana_3 = fecha_3.isocalendar()[1]

    año_3 = fecha_3.isocalendar()[0]

    unidad_3 = distrito_3
    horas_bi = float(horas_3)

    tipos_de_errores_3 = ',' .join(tipo_de_errores_3)

    conteo_3 = len(tipo_de_errores_3)
  
      # ----- Almacenar Lote_3 según municipio seleccionado ---- #
    
    #lote_3_municipios = {"Cabuyaro", "Colombia", "San Luis de Cubarral"}#
    #lote_2_municipios = {"Trinidad", "Iza", "Cuítiva"}#
   
    #if municipio_3 in lote_3_municipios:#
      #lote_3 = '3'#
    #elif municipio_3 in lote_2_municipios:#
      #lote_3 = '2'#
    #else:#
      #lote_3 = '1'#
      # ----- Fin del script ---- #
    
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
        marca_3, usuario, nombre_3, puesto, supervisor_3, "Control de Calidad Precampo Jurídico", fecha_3, semana_3, año_3, distrito_3, tipo_3, 0, aprobados_3, rechazados_3, horas_3,
        manzana_3, sector_3, numero_lote_3, "N/A", 0.0, unidades_catastrales_3, 0, partida_3, 0, 0, "N/A", "N/A",
        "N/A", horas_bi, 0, operador_3, 0, 0, tipos_de_errores_3, conteo_3
      ],
    )
    st.success('Reporte enviado correctamente')
