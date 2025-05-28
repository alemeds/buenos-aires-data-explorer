import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, List, Optional

# Configuración de página
st.set_page_config(
    page_title="Buenos Aires Data Explorer v2.0", 
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

class BuenosAiresCKAN:
    def __init__(self):
        self.base_url = "https://data.buenosaires.gob.ar/api/3/action"
        self.user_agent = 'Buenos Aires Data Explorer Web v2.0'
    
    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        try:
            url = f"{self.base_url}/{endpoint}"
            
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')
                json_data = json.loads(data)
                
                if json_data.get('success'):
                    return json_data.get('result')
                else:
                    st.error(f"Error en la API: {json_data.get('error', 'Error desconocido')}")
                    return None
                    
        except urllib.error.HTTPError as e:
            st.error(f"Error HTTP {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            st.error(f"Error de conexión: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            st.error(f"Error al decodificar JSON: {e}")
            return None
        except Exception as e:
            st.error(f"Error inesperado: {e}")
            return None
    
    def search_packages(self, query: str = "", rows: int = 100) -> Dict:
        params = {
            'q': query,
            'rows': str(rows),
            'sort': 'metadata_modified desc'
        }
        result = self.make_request('package_search', params)
        return result if result else {}
    
    def get_package_info(self, package_id: str) -> Optional[Dict]:
        params = {'id': package_id}
        return self.make_request('package_show', params)
    
    def get_organizations(self) -> List[Dict]:
        params = {'all_fields': 'true'}
        result = self.make_request('organization_list', params)
        return result if result else []

class RealTimeAPI:
    def __init__(self):
        self.user_agent = 'Buenos Aires Data Explorer Web v2.0'
        self.transport_api = "https://api-transporte.buenosaires.gob.ar"
        self.geocoder_api = "https://datosabiertos-apis.buenosaires.gob.ar"
        self.usig_api = "https://servicios.usig.buenosaires.gob.ar"
    
    def make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        try:
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{url}?{query_string}"
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            req.add_header('Accept', 'application/json')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read().decode('utf-8')
                return json.loads(data)
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                st.warning("⚠️  API requiere autenticación")
            elif e.code == 429:
                st.warning("⚠️  Límite de requests excedido")
            else:
                st.error(f"Error HTTP {e.code}: {e.reason}")
            return None
        except Exception as e:
            st.error(f"Error al conectar con API: {e}")
            return None
    
    def get_ecobici_status(self) -> Optional[Dict]:
        url = f"{self.transport_api}/ecobici/gbfs/es/station_status"
        return self.make_api_request(url)
    
    def get_ecobici_stations(self) -> Optional[Dict]:
        url = f"{self.transport_api}/ecobici/gbfs/es/station_information"
        return self.make_api_request(url)
    
    def get_subte_status(self) -> Optional[Dict]:
        url = f"{self.transport_api}/subte/serviceAlerts"
        return self.make_api_request(url)
    
    def get_traffic_info(self) -> Optional[Dict]:
        url = f"{self.transport_api}/transito/cortes"
        return self.make_api_request(url)
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        params = {
            'direccion': address,
            'geocodificar': 'true'
        }
        url = f"{self.usig_api}/normalizar"
        return self.make_api_request(url, params)
    
    def get_air_quality(self) -> Optional[Dict]:
        # Usando World Air Quality Index API (demo)
        url = "https://api.waqi.info/feed/buenos-aires/?token=demo"
        return self.make_api_request(url)

# Inicializar APIs
@st.cache_resource
def init_apis():
    return BuenosAiresCKAN(), RealTimeAPI()

@st.cache_data
def process_datasets(datasets_data):
    if not datasets_data or 'results' not in datasets_data:
        return pd.DataFrame()
    
    datasets = datasets_data['results']
    processed = []
    
    for dataset in datasets:
        org_name = "Sin organización"
        if dataset.get('organization'):
            org_name = dataset['organization'].get('title', 'Sin organización')
        
        formats = []
        if dataset.get('resources'):
            formats = [r.get('format', 'N/A') for r in dataset['resources']]
        
        processed.append({
            'titulo': dataset.get('title', 'Sin título'),
            'organizacion': org_name,
            'fecha_modificacion': dataset.get('metadata_modified', '')[:10],
            'num_recursos': len(dataset.get('resources', [])),
            'formatos': ', '.join(set(formats)) if formats else 'N/A',
            'id': dataset.get('id', ''),
            'descripcion': dataset.get('notes', 'Sin descripción')[:150] + '...' if dataset.get('notes') else 'Sin descripción'
        })
    
    return pd.DataFrame(processed)

def main():
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏙️ Buenos Aires Data Explorer v2.0</h1>
        <p>Datos históricos (CKAN) + Tiempo Real - Ciudad Autónoma de Buenos Aires</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar APIs
    ckan, realtime = init_apis()
    
    # Sidebar
    st.sidebar.title("🗂️ Menú Principal")
    
    # Categorías principales
    categoria = st.sidebar.radio("Selecciona una categoría:", [
        "📊 Datos Históricos (CKAN)",
        "⚡ Datos en Tiempo Real"
    ])
    
    if categoria == "📊 Datos Históricos (CKAN)":
        opcion_historica = st.sidebar.selectbox("Funcionalidad:", [
            "🔍 Buscar Datasets",
            "📋 Datasets Recientes", 
            "🏢 Por Organización",
            "📊 Estadísticas del Portal"
        ])
        
        # === BUSCAR DATASETS ===
        if opcion_historica == "🔍 Buscar Datasets":
            st.title("🔍 Buscar Datasets")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                query = st.text_input("🔎 Término de búsqueda:", placeholder="transporte, salud, economia, seguridad...")
            with col2:
                rows = st.selectbox("📊 Resultados:", [10, 20, 50, 100], index=1)
            
            # Temas populares
            st.write("**🏷️ Temas populares:**")
            temas = ["transporte", "salud", "economia", "seguridad", "educacion", "cultura", "ambiente", "presupuesto"]
            cols = st.columns(4)
            for i, tema in enumerate(temas):
                col_idx = i % 4
                if cols[col_idx].button(f"#{tema}", key=f"tema_{tema}"):
                    st.session_state.query = tema
                    st.rerun()
            
            # Usar query de session state si existe
            if 'query' in st.session_state:
                query = st.session_state.query
            
            # Búsqueda
            if st.button("🔍 Buscar", type="primary") or query:
                with st.spinner(f"🔄 Buscando '{query}'..."):
                    results = ckan.search_packages(query, rows=rows)
                
                if results and results.get('results'):
                    df = process_datasets(results)
                    
                    st.success(f"✅ Encontrados {results.get('count', 0)} datasets (mostrando {len(df)})")
                    
                    # Filtros
                    col1, col2 = st.columns(2)
                    with col1:
                        org_filter = st.selectbox("🏢 Filtrar por organización:", 
                                                ["Todas"] + sorted(df['organizacion'].unique().tolist()))
                    with col2:
                        format_filter = st.selectbox("📁 Filtrar por formato:", 
                                                   ["Todos", "CSV", "JSON", "PDF", "Excel"])
                    
                    # Aplicar filtros
                    df_filtered = df.copy()
                    if org_filter != "Todas":
                        df_filtered = df_filtered[df_filtered['organizacion'] == org_filter]
                    if format_filter != "Todos":
                        df_filtered = df_filtered[df_filtered['formatos'].str.contains(format_filter, na=False)]
                    
                    st.write(f"**📋 Mostrando {len(df_filtered)} resultados:**")
                    
                    # Mostrar resultados
                    for idx, row in df_filtered.iterrows():
                        with st.expander(f"📄 {row['titulo']}", expanded=False):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"**📝 Descripción:** {row['descripcion']}")
                                st.write(f"**🏢 Organización:** {row['organizacion']}")
                            with col2:
                                st.metric("📁 Recursos", row['num_recursos'])
                                st.write(f"**📊 Formatos:** {row['formatos']}")
                                st.write(f"**📅 Actualizado:** {row['fecha_modificacion']}")
                            
                            if st.button(f"🔍 Ver detalles completos", key=f"details_{row['id']}"):
                                with st.spinner("Obteniendo detalles..."):
                                    detailed_info = ckan.get_package_info(row['id'])
                                if detailed_info:
                                    st.subheader("📋 Información Detallada")
                                    
                                    # Información básica
                                    st.write(f"**🔖 ID:** {detailed_info.get('name')}")
                                    st.write(f"**📝 Descripción completa:** {detailed_info.get('notes', 'No disponible')}")
                                    
                                    # Recursos
                                    resources = detailed_info.get('resources', [])
                                    if resources:
                                        st.subheader(f"💾 Recursos Disponibles ({len(resources)})")
                                        for i, resource in enumerate(resources, 1):
                                            name = resource.get('name') or f"Recurso {i}"
                                            format_type = resource.get('format', 'N/A').upper()
                                            url = resource.get('url', '')
                                            
                                            st.write(f"**{i}. {name}** ({format_type})")
                                            if url:
                                                st.write(f"🔗 [Descargar]({url})")
                else:
                    st.warning("❌ No se encontraron resultados para tu búsqueda.")
        
        # === DATASETS RECIENTES ===
        elif opcion_historica == "📋 Datasets Recientes":
            st.title("📋 Datasets Recientes")
            
            num_datasets = st.slider("📊 Número de datasets a mostrar:", 5, 50, 15)
            
            if st.button("🔄 Cargar Datasets Recientes", type="primary"):
                with st.spinner("📥 Cargando datasets más recientes..."):
                    results = ckan.search_packages("", rows=num_datasets)
                
                if results and results.get('results'):
                    df = process_datasets(results)
                    
                    st.success(f"✅ Cargados {len(df)} datasets más recientes")
                    
                    # Tabla interactiva
                    st.dataframe(
                        df[['titulo', 'organizacion', 'fecha_modificacion', 'num_recursos', 'formatos']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "titulo": "📄 Título",
                            "organizacion": "🏢 Organización", 
                            "fecha_modificacion": "📅 Fecha",
                            "num_recursos": "📁 Recursos",
                            "formatos": "📊 Formatos"
                        }
                    )
                    
                    # Gráfico
                    org_counts = df['organizacion'].value_counts().head(8)
                    fig = px.bar(
                        x=org_counts.values, 
                        y=org_counts.index,
                        orientation='h',
                        title="🏆 Top Organizaciones - Datasets Recientes",
                        labels={'x': 'Número de Datasets', 'y': 'Organización'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        # === POR ORGANIZACIÓN ===
        elif opcion_historica == "🏢 Por Organización":
            st.title("🏢 Datasets por Organización")
            
            if st.button("📥 Cargar Organizaciones", type="primary"):
                with st.spinner("🔄 Cargando organizaciones..."):
                    orgs = ckan.get_organizations()
                
                if orgs:
                    orgs_sorted = sorted(orgs, key=lambda x: x.get('package_count', 0), reverse=True)
                    
                    # Mostrar top 10
                    st.subheader("🏆 Top 10 Organizaciones")
                    
                    top_10 = orgs_sorted[:10]
                    org_data = []
                    for org in top_10:
                        org_data.append({
                            'Organización': org.get('display_name', org.get('name', 'Sin nombre')),
                            'Datasets': org.get('package_count', 0),
                            'Seguidores': org.get('num_followers', 0),
                            'ID': org.get('name', '')
                        })
                    
                    df_orgs = pd.DataFrame(org_data)
                    st.dataframe(df_orgs[['Organización', 'Datasets', 'Seguidores']], use_container_width=True, hide_index=True)
                    
                    # Selector para ver datasets
                    selected_org_name = st.selectbox("🔍 Selecciona una organización para ver sus datasets:", 
                                                    df_orgs['Organización'].tolist())
                    
                    if st.button("📋 Ver Datasets de esta Organización"):
                        # Encontrar ID de la organización seleccionada
                        selected_org_id = df_orgs[df_orgs['Organización'] == selected_org_name]['ID'].iloc[0]
                        
                        with st.spinner(f"📥 Cargando datasets de {selected_org_name}..."):
                            query = f"organization:{selected_org_id}"
                            results = ckan.search_packages(query, rows=30)
                        
                        if results and results.get('results'):
                            df_org_datasets = process_datasets(results)
                            st.success(f"✅ {len(df_org_datasets)} datasets de {selected_org_name}")
                            
                            st.dataframe(
                                df_org_datasets[['titulo', 'fecha_modificacion', 'num_recursos', 'formatos']], 
                                use_container_width=True, 
                                hide_index=True,
                                column_config={
                                    "titulo": "📄 Título",
                                    "fecha_modificacion": "📅 Fecha",
                                    "num_recursos": "📁 Recursos", 
                                    "formatos": "📊 Formatos"
                                }
                            )
        
        # === ESTADÍSTICAS ===
        elif opcion_historica == "📊 Estadísticas del Portal":
            st.title("📊 Estadísticas del Portal")
            
            if st.button("📈 Cargar Estadísticas", type="primary"):
                with st.spinner("📊 Obteniendo estadísticas..."):
                    stats = ckan.search_packages("", rows=1)
                    orgs = ckan.get_organizations()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_datasets = stats.get('count', 0) if stats else 0
                    st.metric("📄 Total Datasets", f"{total_datasets:,}")
                
                with col2:
                    total_orgs = len(orgs) if orgs else 0
                    st.metric("🏢 Organizaciones", total_orgs)
                
                with col3:
                    st.metric("🔗 APIs Disponibles", "12+")
                
                if orgs:
                    st.subheader("🏆 Top 5 Organizaciones")
                    orgs_sorted = sorted(orgs, key=lambda x: x.get('package_count', 0), reverse=True)[:5]
                    
                    for i, org in enumerate(orgs_sorted, 1):
                        name = org.get('display_name', org.get('name', 'Sin nombre'))
                        count = org.get('package_count', 0)
                        st.write(f"**{i}.** {name}: **{count}** datasets")
    
    # === DATOS EN TIEMPO REAL ===
    else:
        opcion_realtime = st.sidebar.selectbox("Funcionalidad:", [
            "🚇 Transporte Público",
            "🚦 Estado del Tránsito", 
            "🌫️ Calidad del Aire",
            "📍 Geocodificación",
            "🗺️ Servicios por Ubicación"
        ])
        
        # === TRANSPORTE PÚBLICO ===
        if opcion_realtime == "🚇 Transporte Público":
            st.title("🚇 Transporte Público en Tiempo Real")
            
            tab1, tab2, tab3 = st.tabs(["🚴 Ecobici", "🚇 Subte", "🚦 Tránsito"])
            
            with tab1:
                st.subheader("🚴 Estado de Ecobici")
                
                if st.button("🔄 Actualizar Estado Ecobici", type="primary"):
                    with st.spinner("📡 Obteniendo datos de Ecobici..."):
                        status_data = realtime.get_ecobici_status()
                    
                    if status_data and 'data' in status_data:
                        stations = status_data['data'].get('stations', [])
                        
                        if stations:
                            df_stations = pd.DataFrame(stations)
                            
                            # Métricas principales
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                total_bikes = df_stations['num_bikes_available'].sum()
                                st.metric("🚴 Bicicletas", total_bikes)
                            with col2:
                                total_docks = df_stations['num_docks_available'].sum()
                                st.metric("🔗 Lugares", total_docks)
                            with col3:
                                active_stations = len(df_stations[df_stations['is_renting'] == 1])
                                st.metric("🟢 Activas", active_stations)
                            with col4:
                                total_stations = len(df_stations)
                                st.metric("📍 Total", total_stations)
                            
                            # Gráfico top estaciones
                            top_stations = df_stations.nlargest(10, 'num_bikes_available')
                            
                            fig = px.bar(
                                top_stations, 
                                x='station_id', 
                                y='num_bikes_available',
                                title="🏆 Top 10 Estaciones - Más Bicicletas",
                                labels={'num_bikes_available': 'Bicicletas', 'station_id': 'ID Estación'}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Distribución de disponibilidad
                            fig2 = px.histogram(
                                df_stations, 
                                x='num_bikes_available',
                                title="📊 Distribución de Bicicletas por Estación",
                                labels={'num_bikes_available': 'Bicicletas Disponibles', 'count': 'Número de Estaciones'}
                            )
                            st.plotly_chart(fig2, use_container_width=True)
                            
                            # Tabla detallada (solo primeras 20)
                            st.subheader("📋 Estado Detallado (Primeras 20 estaciones)")
                            display_df = df_stations.head(20)[['station_id', 'num_bikes_available', 'num_docks_available', 'is_renting']].copy()
                            display_df['is_renting'] = display_df['is_renting'].map({1: '✅', 0: '❌'})
                            display_df.columns = ['ID', 'Bicicletas', 'Lugares', 'Activa']
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("⚠️ No se obtuvieron datos de estaciones")
                    else:
                        st.error("❌ No se pudo conectar con la API de Ecobici")
                        st.info("🔗 API: https://api-transporte.buenosaires.gob.ar")
            
            with tab2:
                st.subheader("🚇 Estado del Subte")
                
                if st.button("🔄 Actualizar Estado Subte", type="primary"):
                    with st.spinner("📡 Obteniendo alertas del subte..."):
                        subte_data = realtime.get_subte_status()
                    
                    if subte_data:
                        alerts = subte_data.get('entity', [])
                        
                        if alerts:
                            st.warning(f"⚠️ {len(alerts)} alertas activas")
                            
                            for i, alert in enumerate(alerts[:5], 1):
                                alert_info = alert.get('alert', {})
                                description = alert_info.get('description_text', {}).get('translation', [])
                                
                                if description:
                                    text = description[0].get('text', 'Sin descripción')
                                    st.error(f"**🚨 Alerta {i}:** {text[:150]}...")
                        else:
                            st.markdown("""
                            <div class="success-box">
                                <h4>✅ Sistema Funcionando Normalmente</h4>
                                <p>🚇 No hay alertas activas en el sistema de subte</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("❌ No se pudo obtener información del subte")
            
            with tab3:
                st.subheader("🚦 Estado del Tránsito")
                
                if st.button("🔄 Actualizar Estado Tránsito", type="primary"):
                    with st.spinner("📡 Obteniendo información de tránsito..."):
                        traffic_data = realtime.get_traffic_info()
                    
                    if traffic_data:
                        cortes = traffic_data.get('cortes', []) if isinstance(traffic_data, dict) else []
                        
                        if cortes:
                            st.warning(f"🚧 {len(cortes)} cortes de tránsito activos")
                            
                            for i, corte in enumerate(cortes[:10], 1):
                                calle = corte.get('calle', 'N/A')
                                motivo = corte.get('motivo', 'Sin especificar')
                                desde = corte.get('desde', '')
                                hasta = corte.get('hasta', '')
                                
                                st.error(f"**🚧 Corte {i}:** {calle}")
                                if desde or hasta:
                                    st.write(f"   📍 Desde: {desde} - Hasta: {hasta}")
                                st.write(f"   📝 Motivo: {motivo}")
                        else:
                            st.markdown("""
                            <div class="success-box">
                                <h4>✅ Tráfico Normal</h4>
                                <p>🚗 No hay cortes de tránsito reportados</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("❌ No se pudo obtener información de tránsito")
        
        # === CALIDAD DEL AIRE ===
        elif opcion_realtime == "🌫️ Calidad del Aire":
            st.title("🌫️ Calidad del Aire")
            
            if st.button("🔄 Obtener Calidad del Aire", type="primary"):
                with st.spinner("🌍 Obteniendo datos de calidad del aire..."):
                    air_data = realtime.get_air_quality()
                
                if air_data and air_data.get('status') == 'ok':
                    data = air_data.get('data', {})
                    aqi = data.get('aqi', 'N/A')
                    
                    # Métricas principales
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if isinstance(aqi, int):
                            if aqi <= 50:
                                st.metric("🌟 AQI", aqi, "🟢 Bueno")
                            elif aqi <= 100:
                                st.metric("⚠️ AQI", aqi, "🟡 Moderado")
                            else:
                                st.metric("❌ AQI", aqi, "🔴 Dañino")
                        else:
                            st.metric("📊 AQI", "N/A", "❓ No disponible")
                    
                    with col2:
                        city = data.get('city', {}).get('name', 'Buenos Aires')
                        st.metric("📍 Estación", city)
                    
                    with col3:
                        time_data = data.get('time', {}).get('s', 'N/A')
                        st.metric("🕐 Actualización", time_data[:10] if time_data != 'N/A' else 'N/A')
                    
                    # Contaminantes específicos
                    iaqi = data.get('iaqi', {})
                    if iaqi:
                        st.subheader("🧪 Contaminantes Específicos")
                        
                        contaminants_data = []
                        for contaminant, value in iaqi.items():
                            if isinstance(value, dict) and 'v' in value:
                                contaminants_data.append({
                                    'Contaminante': contaminant.upper(),
                                    'Valor': value['v']
                                })
                        
                        if contaminants_data:
                            df_contaminants = pd.DataFrame(contaminants_data)
                            st.dataframe(df_contaminants, use_container_width=True, hide_index=True)
                            
                            # Gráfico de contaminantes
                            fig = px.bar(
                                df_contaminants, 
                                x='Contaminante', 
                                y='Valor',
                                title="📊 Niveles de Contaminantes",
                                labels={'Valor': 'Índice', 'Contaminante': 'Tipo'}
                            )
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    # Datos de demostración
                    st.markdown("""
                    <div class="warning-box">
                        <h4>⚠️ Datos de Demostración</h4>
                        <p>Para datos reales, registrarse en APIs de calidad del aire</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("🌟 AQI Estimado", "45-65", "🟢 Bueno")
                    with col2:
                        st.metric("📍 Ciudad", "Buenos Aires")
                    with col3:
                        st.metric("🕐 Estado", "Demo")
                    
                    st.info("🔗 Consulta datos reales en: https://aqicn.org/city/buenos-aires/es/")
        
        # === GEOCODIFICACIÓN ===
        elif opcion_realtime == "📍 Geocodificación":
            st.title("📍 Geocodificación de Direcciones")
            
            st.write("🗺️ Convierte direcciones de CABA en coordenadas geográficas")
            
            address = st.text_input("📍 Ingresa una dirección:", placeholder="Av. Corrientes 1000, CABA")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                geocode_btn = st.button("🔍 Geocodificar", type="primary")
            with col2:
                if address:
                    st.write(f"**Dirección a geocodificar:** {address}")
            
            if geocode_btn and address:
                with st.spinner(f"🗺️ Geocodificando: {address}"):
                    geo_data = realtime.geocode_address(address)
                
                if geo_data:
                    st.success("✅ Dirección geocodificada exitosamente")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📍 Resultados")
                        
                        # Dirección normalizada
                        direccion_norm = geo_data.get('direccion', address)
                        st.write(f"**🏠 Dirección normalizada:** {direccion_norm}")
                        
                        # Coordenadas
                        coordenadas = geo_data.get('coordenadas', {})
                        if coordenadas:
                            lat = coordenadas.get('lat', 'N/A')
                            lng = coordenadas.get('lng', 'N/A')
                            
                            st.metric("🌐 Latitud", lat)
                            st.metric("🌐 Longitud", lng)
                            
                            if lat != 'N/A' and lng != 'N/A':
                                # Crear mapa simple
                                map_data = pd.DataFrame({'lat': [float(lat)], 'lon': [float(lng)]})
                                st.map(map_data, zoom=15)
                        
                        # Información adicional
                        extra_info = {}
                        for key in ['barrio', 'comuna', 'codigo_postal']:
                            if key in geo_data:
                                extra_info[key] = geo_data[key]
                        
                        if extra_info:
                            st.subheader("📋 Información Adicional")
                            for key, value in extra_info.items():
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    
                    with col2:
                        st.subheader("🔍 Respuesta Completa de la API")
                        st.json(geo_data)
                
                else:
                    st.error("❌ No se pudo geocodificar la dirección")
                    st.info("💡 Intenta con una dirección más específica (ej: 'Av. Corrientes 1000')")
        
        # === SERVICIOS POR UBICACIÓN ===
        elif opcion_realtime == "🗺️ Servicios por Ubicación":
            st.title("🗺️ Servicios Útiles por Ubicación")
            
            st.write("🔍 Obtén información de servicios públicos por coordenadas o dirección")
            
            # Opciones de consulta
            metodo = st.radio("📍 Método de consulta:", ["Por dirección", "Por coordenadas"])
            
            if metodo == "Por dirección":
                address = st.text_input("🏠 Dirección:", placeholder="Florida 300, CABA")
                
                if st.button("🔍 Buscar Servicios", type="primary") and address:
                    with st.spinner("🗺️ Geocodificando dirección..."):
                        geo_data = realtime.geocode_address(address)
                    
                    if geo_data and geo_data.get('coordenadas'):
                        lat = geo_data['coordenadas'].get('lat')
                        lng = geo_data['coordenadas'].get('lng')
                        
                        if lat and lng:
                            st.success(f"✅ Dirección encontrada: {lat}, {lng}")
                            
                            # Simulación de datos útiles (la API real podría no estar disponible)
                            st.subheader("📍 Información de Ubicación")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("🏘️ Barrio", "San Nicolás")
                                st.metric("👮 Comisaría", "1ra")
                            with col2:
                                st.metric("🏛️ Comuna", "1")
                                st.metric("🏥 Área Hospitalaria", "Centro")
                            with col3:
                                st.metric("📬 Código Postal", "C1005")
                                st.metric("🚇 Subte más cercano", "Línea B")
                            
                            st.info("⚠️ Datos simulados - Para información real, verificar APIs específicas")
                        else:
                            st.error("❌ No se pudieron obtener coordenadas")
                    else:
                        st.error("❌ No se pudo geocodificar la dirección")
            
            else:  # Por coordenadas
                col1, col2 = st.columns(2)
                with col1:
                    lat = st.number_input("🌐 Latitud:", value=-34.6037, format="%.6f")
                with col2:
                    lng = st.number_input("🌐 Longitud:", value=-58.3816, format="%.6f")
                
                if st.button("🔍 Buscar Servicios", type="primary"):
                    st.success(f"✅ Coordenadas: {lat}, {lng}")
                    
                    # Crear mapa
                    map_data = pd.DataFrame({'lat': [lat], 'lon': [lng]})
                    st.map(map_data, zoom=15)
                    
                    # Simulación de servicios por ubicación
                    st.subheader("📍 Servicios en esta Ubicación")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write("**🏘️ Barrio:** Puerto Madero")
                        st.write("**🏛️ Comuna:** 1")
                    with col2:
                        st.write("**👮 Comisaría:** 1ra")
                        st.write("**🏥 Hospital:** Argerich")
                    with col3:
                        st.write("**📬 CP:** C1107")
                        st.write("**🚇 Subte:** Línea E")
                    
                    st.info("⚠️ Datos simulados para demostración")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🏙️ <strong>Buenos Aires Data Explorer v2.0</strong> | 
        Datos del <a href="https://data.buenosaires.gob.ar/" target="_blank">Portal de Datos Abiertos GCBA</a> | 
        APIs en Tiempo Real</p>
        <p style="font-size: 0.8em;">💻 Desarrollado con Streamlit + Python | 
        📡 Sin dependencias externas de requests</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
