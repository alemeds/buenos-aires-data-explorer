#!/usr/bin/env python3
"""
Buenos Aires CKAN Data Explorer - Versión con Datos en Tiempo Real
Programa para explorar datos históricos (CKAN) y en tiempo real de Buenos Aires
Solo usa librerías incluidas en Python 3
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class BuenosAiresCKAN:
    def __init__(self):
        self.base_url = "https://data.buenosaires.gob.ar/api/3/action"
        self.user_agent = 'Buenos Aires Data Explorer/2.0'
    
    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Realiza una petición a la API de CKAN usando urllib"""
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
                    print(f"Error en la API: {json_data.get('error', 'Error desconocido')}")
                    return None
                    
        except urllib.error.HTTPError as e:
            print(f"Error HTTP {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            print(f"Error de conexión: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None
    
    def get_package_list(self) -> List[str]:
        """Obtiene la lista de todos los datasets"""
        result = self.make_request('package_list')
        return result if result else []
    
    def search_packages(self, query: str = "", rows: int = 100) -> Dict:
        """Busca datasets por término de búsqueda"""
        params = {
            'q': query,
            'rows': str(rows),
            'sort': 'metadata_modified desc'
        }
        result = self.make_request('package_search', params)
        return result if result else {}
    
    def get_package_info(self, package_id: str) -> Optional[Dict]:
        """Obtiene información detallada de un dataset"""
        params = {'id': package_id}
        return self.make_request('package_show', params)
    
    def get_organizations(self) -> List[Dict]:
        """Obtiene la lista de organizaciones"""
        params = {'all_fields': 'true'}
        result = self.make_request('organization_list', params)
        return result if result else []
    
    def download_resource(self, url: str, filename: str) -> bool:
        """Descarga un recurso (archivo) del dataset usando urllib"""
        try:
            print(f"Descargando: {filename}")
            
            os.makedirs('downloads', exist_ok=True)
            filepath = os.path.join('downloads', filename)
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(req, timeout=60) as response:
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            
            print(f"✓ Descarga completada: {filepath}")
            return True
            
        except urllib.error.HTTPError as e:
            print(f"✗ Error HTTP al descargar {filename}: {e.code} {e.reason}")
            return False
        except urllib.error.URLError as e:
            print(f"✗ Error de conexión al descargar {filename}: {e.reason}")
            return False
        except Exception as e:
            print(f"✗ Error al descargar {filename}: {e}")
            return False

class RealTimeAPI:
    """Clase para manejar APIs de datos en tiempo real"""
    
    def __init__(self):
        self.user_agent = 'Buenos Aires Data Explorer/2.0'
        self.transport_api = "https://api-transporte.buenosaires.gob.ar"
        self.geocoder_api = "https://datosabiertos-apis.buenosaires.gob.ar"
        self.usig_api = "https://servicios.usig.buenosaires.gob.ar"
    
    def make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Realiza petición a APIs externas"""
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
            print(f"Error HTTP {e.code}: {e.reason}")
            if e.code == 401:
                print("⚠️  API requiere autenticación")
            elif e.code == 429:
                print("⚠️  Límite de requests excedido")
            return None
        except urllib.error.URLError as e:
            print(f"Error de conexión: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error al decodificar respuesta: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado: {e}")
            return None
    
    def get_ecobici_status(self) -> Optional[Dict]:
        """Obtiene estado actual del sistema Ecobici"""
        url = f"{self.transport_api}/ecobici/gbfs/es/station_status"
        return self.make_api_request(url)
    
    def get_ecobici_stations(self) -> Optional[Dict]:
        """Obtiene información de estaciones Ecobici"""
        url = f"{self.transport_api}/ecobici/gbfs/es/station_information"
        return self.make_api_request(url)
    
    def get_subte_status(self) -> Optional[Dict]:
        """Obtiene estado de líneas de subte"""
        url = f"{self.transport_api}/subte/serviceAlerts"
        return self.make_api_request(url)
    
    def get_traffic_info(self) -> Optional[Dict]:
        """Obtiene información de tránsito"""
        url = f"{self.transport_api}/transito/cortes"
        return self.make_api_request(url)
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Geocodifica una dirección"""
        params = {
            'direccion': address,
            'geocodificar': 'true'
        }
        url = f"{self.usig_api}/normalizar"
        return self.make_api_request(url, params)
    
    def get_useful_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Obtiene datos útiles por coordenadas"""
        params = {
            'lat': str(lat),
            'lng': str(lng)
        }
        url = f"{self.geocoder_api}/BA_Root/datos_utiles"
        return self.make_api_request(url, params)
    
    def get_air_quality(self) -> Optional[Dict]:
        """Obtiene calidad del aire (usando API externa)"""
        # Usando World Air Quality Index API (gratuita)
        url = "https://api.waqi.info/feed/buenos-aires/?token=demo"
        return self.make_api_request(url)
    
    def get_weather_data(self) -> Optional[Dict]:
        """Obtiene datos meteorológicos básicos"""
        # Usar OpenWeatherMap o similar (aquí simulo estructura)
        print("⚠️  Para datos meteorológicos precisos, considere registrarse en OpenWeatherMap API")
        return {
            "status": "demo",
            "message": "Registrese en OpenWeatherMap para datos reales",
            "demo_data": {
                "temperature": "18°C",
                "humidity": "65%",
                "description": "Parcialmente nublado"
            }
        }

class MenuExplorer:
    def __init__(self):
        self.ckan = BuenosAiresCKAN()
        self.realtime = RealTimeAPI()
        self.current_datasets = []
    
    def mostrar_menu_principal(self):
        """Muestra el menú principal"""
        print("\n" + "="*70)
        print("🏙️  EXPLORADOR DE DATOS ABIERTOS - BUENOS AIRES v2.0")
        print("="*70)
        print("📊 DATOS HISTÓRICOS (CKAN):")
        print("  1. 🔍 Buscar datasets por tema")
        print("  2. 📋 Listar datasets recientes")
        print("  3. 🏢 Ver datasets por organización")
        print("  4. 📄 Ver detalles de un dataset específico")
        print("  5. 💾 Descargar recursos de un dataset")
        print("  6. 📈 Mostrar estadísticas del portal")
        print("\n⚡ DATOS EN TIEMPO REAL:")
        print("  7. 🚇 Transporte público (subte, colectivos, ecobici)")
        print("  8. 🚦 Estado del tránsito y cortes")
        print("  9. 🌫️ Calidad del aire")
        print(" 10. 🌤️  Datos meteorológicos")
        print(" 11. 📍 Geocodificación y datos por ubicación")
        print(" 12. 🗺️  Servicios útiles por dirección")
        print("\n 0. 🚪 Salir")
        print("="*70)
    
    def buscar_por_tema(self):
        """Busca datasets por tema/palabra clave"""
        print("\n🔍 BÚSQUEDA POR TEMA")
        print("-" * 30)
        
        temas_populares = [
            "transporte", "salud", "economia", "seguridad", "educacion",
            "cultura", "ambiente", "turismo", "obras", "presupuesto"
        ]
        print("Temas populares:", ", ".join(temas_populares))
        
        query = input("\nIngresa término de búsqueda (o Enter para ver todos): ").strip()
        
        print(f"\nBuscando datasets con '{query}'...")
        result = self.ckan.search_packages(query, rows=20)
        
        if not result:
            print("No se pudieron obtener resultados.")
            return
        
        datasets = result.get('results', [])
        total_count = result.get('count', 0)
        
        print(f"\n📊 Encontrados {total_count} datasets (mostrando primeros 20)")
        print("-" * 50)
        
        self.current_datasets = datasets
        self.mostrar_lista_datasets(datasets)
    
    def listar_recientes(self):
        """Lista los datasets más recientes"""
        print("\n📋 DATASETS RECIENTES")
        print("-" * 30)
        
        result = self.ckan.search_packages("", rows=15)
        if not result:
            print("No se pudieron obtener los datasets.")
            return
        
        datasets = result.get('results', [])
        self.current_datasets = datasets
        self.mostrar_lista_datasets(datasets)
    
    def ver_por_organizacion(self):
        """Muestra datasets agrupados por organización"""
        print("\n🏢 DATASETS POR ORGANIZACIÓN")
        print("-" * 40)
        
        print("Obteniendo organizaciones...")
        orgs = self.ckan.get_organizations()
        if not orgs:
            print("No se pudieron obtener las organizaciones.")
            return
        
        orgs_sorted = sorted(orgs, key=lambda x: x.get('package_count', 0), reverse=True)[:10]
        
        print("Top 10 organizaciones con más datasets:")
        for i, org in enumerate(orgs_sorted, 1):
            name = org.get('display_name', org.get('name', 'Sin nombre'))
            count = org.get('package_count', 0)
            print(f"{i:2d}. {name} ({count} datasets)")
        
        try:
            choice = int(input(f"\nSelecciona una organización (1-{len(orgs_sorted)}): "))
            if 1 <= choice <= len(orgs_sorted):
                org_name = orgs_sorted[choice-1]['name']
                self.buscar_por_organizacion(org_name)
        except ValueError:
            print("Selección inválida.")
    
    def buscar_por_organizacion(self, org_name: str):
        """Busca datasets de una organización específica"""
        query = f"organization:{org_name}"
        result = self.ckan.search_packages(query, rows=20)
        
        if result:
            datasets = result.get('results', [])
            self.current_datasets = datasets
            print(f"\nDatasets de la organización:")
            self.mostrar_lista_datasets(datasets)
    
    def mostrar_lista_datasets(self, datasets: List[Dict]):
        """Muestra una lista numerada de datasets"""
        if not datasets:
            print("No hay datasets para mostrar.")
            return
        
        for i, dataset in enumerate(datasets, 1):
            title = dataset.get('title', dataset.get('name', 'Sin título'))
            notes = dataset.get('notes', 'Sin descripción')
            
            if len(notes) > 100:
                notes = notes[:100] + "..."
            
            modified = dataset.get('metadata_modified', '')
            if modified:
                try:
                    if 'T' in modified:
                        date_part = modified.split('T')[0]
                        date_obj = datetime.strptime(date_part, '%Y-%m-%d')
                        modified = date_obj.strftime('%d/%m/%Y')
                    else:
                        modified = modified[:10]
                except:
                    modified = modified[:10] if len(modified) >= 10 else modified
            
            print(f"\n{i:2d}. 📄 {title}")
            print(f"     📝 {notes}")
            if modified:
                print(f"     📅 Actualizado: {modified}")
            
            resources = dataset.get('resources', [])
            if resources:
                formats = []
                for r in resources:
                    fmt = r.get('format', 'N/A').upper()
                    if fmt not in formats:
                        formats.append(fmt)
                print(f"     💾 Formatos: {', '.join(formats)}")
    
    def ver_detalles_dataset(self):
        """Muestra detalles de un dataset específico"""
        if not self.current_datasets:
            print("\nPrimero debes buscar datasets.")
            return
        
        try:
            choice = int(input(f"\nSelecciona un dataset (1-{len(self.current_datasets)}): "))
            if 1 <= choice <= len(self.current_datasets):
                dataset = self.current_datasets[choice-1]
                self.mostrar_detalles_completos(dataset)
        except ValueError:
            print("Selección inválida.")
    
    def mostrar_detalles_completos(self, dataset: Dict):
        """Muestra información detallada de un dataset"""
        package_id = dataset.get('id') or dataset.get('name')
        print(f"\nObteniendo detalles de: {package_id}")
        
        detailed_info = self.ckan.get_package_info(package_id)
        
        if not detailed_info:
            print("No se pudo obtener información detallada.")
            return
        
        print("\n" + "="*60)
        print(f"📄 {detailed_info.get('title', 'Sin título')}")
        print("="*60)
        
        print(f"🔖 ID: {detailed_info.get('name')}")
        
        notes = detailed_info.get('notes', 'No disponible')
        print(f"📝 Descripción: {notes}")
        
        org = detailed_info.get('organization', {})
        if org:
            org_name = org.get('title', org.get('name', 'N/A'))
            print(f"🏢 Organización: {org_name}")
        
        created = detailed_info.get('metadata_created', '')
        modified = detailed_info.get('metadata_modified', '')
        if created:
            print(f"📅 Creado: {created[:10]}")
        if modified:
            print(f"🔄 Actualizado: {modified[:10]}")
        
        tags = detailed_info.get('tags', [])
        if tags:
            tag_names = []
            for tag in tags:
                if isinstance(tag, dict) and tag.get('name'):
                    tag_names.append(tag.get('name'))
                elif isinstance(tag, str):
                    tag_names.append(tag)
            
            if tag_names:
                print(f"🏷️  Tags: {', '.join(tag_names)}")
        
        resources = detailed_info.get('resources', [])
        if resources:
            print(f"\n💾 RECURSOS DISPONIBLES ({len(resources)}):")
            print("-" * 40)
            for i, resource in enumerate(resources, 1):
                name = resource.get('name') or resource.get('description') or f"Recurso {i}"
                format_type = resource.get('format', 'N/A').upper()
                size = resource.get('size')
                size_str = f" ({size} bytes)" if size else ""
                
                print(f"{i}. {name}")
                print(f"   📊 Formato: {format_type}{size_str}")
                
                url = resource.get('url')
                if url:
                    display_url = url if len(url) <= 80 else url[:77] + "..."
                    print(f"   🔗 URL: {display_url}")
    
    def descargar_recursos(self):
        """Permite descargar recursos de un dataset seleccionado"""
        if not self.current_datasets:
            print("\nPrimero debes buscar datasets.")
            return
        
        try:
            choice = int(input(f"\nSelecciona un dataset para descargar (1-{len(self.current_datasets)}): "))
            if 1 <= choice <= len(self.current_datasets):
                dataset = self.current_datasets[choice-1]
                self.descargar_recursos_dataset(dataset)
        except ValueError:
            print("Selección inválida.")
    
    def descargar_recursos_dataset(self, dataset: Dict):
        """Descarga recursos de un dataset específico"""
        package_id = dataset.get('id') or dataset.get('name')
        print(f"\nObteniendo recursos de: {package_id}")
        
        detailed_info = self.ckan.get_package_info(package_id)
        
        if not detailed_info:
            print("No se pudo obtener información del dataset.")
            return
        
        resources = detailed_info.get('resources', [])
        if not resources:
            print("Este dataset no tiene recursos para descargar.")
            return
        
        print(f"\n💾 RECURSOS DE: {detailed_info.get('title')}")
        print("-" * 50)
        
        for i, resource in enumerate(resources, 1):
            name = resource.get('name') or resource.get('description') or f"Recurso {i}"
            format_type = resource.get('format', 'N/A').upper()
            print(f"{i}. {name} ({format_type})")
        
        print(f"{len(resources)+1}. Descargar todos")
        print("0. Volver")
        
        try:
            choice = int(input(f"\nSelecciona qué descargar (0-{len(resources)+1}): "))
            
            if choice == 0:
                return
            elif choice == len(resources) + 1:
                for resource in resources:
                    self.descargar_recurso_individual(resource, detailed_info.get('name'))
            elif 1 <= choice <= len(resources):
                resource = resources[choice-1]
                self.descargar_recurso_individual(resource, detailed_info.get('name'))
        except ValueError:
            print("Selección inválida.")
    
    def descargar_recurso_individual(self, resource: Dict, dataset_name: str):
        """Descarga un recurso individual"""
        url = resource.get('url')
        if not url:
            print("Este recurso no tiene URL de descarga.")
            return
        
        name = resource.get('name') or resource.get('description') or 'recurso'
        format_type = resource.get('format', '').lower()
        
        safe_name = self.clean_filename(name)
        safe_dataset = self.clean_filename(dataset_name or 'dataset')
        
        if format_type and not safe_name.endswith(f'.{format_type}'):
            filename = f"{safe_dataset}_{safe_name}.{format_type}"
        else:
            filename = f"{safe_dataset}_{safe_name}"
        
        self.ckan.download_resource(url, filename)
    
    def clean_filename(self, filename: str) -> str:
        """Limpia un nombre de archivo de caracteres especiales"""
        clean_chars = []
        for char in filename:
            if char.isalnum() or char in (' ', '-', '_', '.'):
                clean_chars.append(char)
            else:
                clean_chars.append('_')
        
        result = ''.join(clean_chars).strip()
        result = ' '.join(result.split())
        result = result.replace(' ', '_')
        
        return result[:50]
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas generales del portal"""
        print("\n📈 ESTADÍSTICAS DEL PORTAL")
        print("-" * 40)
        
        print("Obteniendo estadísticas...")
        
        result = self.ckan.search_packages("", rows=1)
        if result:
            total_datasets = result.get('count', 0)
            print(f"📊 Total de datasets: {total_datasets}")
        
        orgs = self.ckan.get_organizations()
        if orgs:
            print(f"🏢 Total de organizaciones: {len(orgs)}")
            
            orgs_sorted = sorted(orgs, key=lambda x: x.get('package_count', 0), reverse=True)[:5]
            print("\n🏆 Top 5 organizaciones:")
            for i, org in enumerate(orgs_sorted, 1):
                name = org.get('display_name', org.get('name', 'Sin nombre'))
                count = org.get('package_count', 0)
                print(f"  {i}. {name}: {count} datasets")
    
    # NUEVAS FUNCIONES PARA DATOS EN TIEMPO REAL
    
    def mostrar_transporte_publico(self):
        """Muestra información de transporte público en tiempo real"""
        print("\n🚇 TRANSPORTE PÚBLICO EN TIEMPO REAL")
        print("-" * 50)
        
        while True:
            print("\n1. 🚴 Estado de Ecobici (bicicletas públicas)")
            print("2. 🚇 Estado del Subte")
            print("3. 🚌 Información de Colectivos")
            print("0. 🔙 Volver al menú principal")
            
            try:
                choice = input("\nSelecciona una opción: ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self.mostrar_ecobici_status()
                elif choice == '2':
                    self.mostrar_subte_status()
                elif choice == '3':
                    self.mostrar_colectivos_info()
                else:
                    print("⚠️  Opción inválida.")
                    
                if choice in ['1', '2', '3']:
                    input("\nPresiona Enter para continuar...")
                    
            except KeyboardInterrupt:
                break
    
    def mostrar_ecobici_status(self):
        """Muestra el estado actual de las estaciones Ecobici"""
        print("\n🚴 ESTADO DE ECOBICI")
        print("-" * 30)
        
        print("Obteniendo estado de estaciones...")
        status_data = self.realtime.get_ecobici_status()
        stations_data = self.realtime.get_ecobici_stations()
        
        if not status_data and not stations_data:
            print("❌ No se pudo obtener información de Ecobici")
            print("🔗 Intenta acceder directamente a: https://api-transporte.buenosaires.gob.ar")
            return
        
        if status_data:
            stations = status_data.get('data', {}).get('stations', [])
            if stations:
                print(f"\n📊 Estado de {len(stations)} estaciones:")
                
                # Mostrar resumen
                available_bikes = sum(s.get('num_bikes_available', 0) for s in stations)
                available_docks = sum(s.get('num_docks_available', 0) for s in stations)
                
                print(f"🚴 Bicicletas disponibles: {available_bikes}")
                print(f"🔗 Lugares disponibles: {available_docks}")
                
                # Mostrar top 10 estaciones con más bicicletas
                stations_sorted = sorted(stations, 
                                       key=lambda x: x.get('num_bikes_available', 0), 
                                       reverse=True)[:10]
                
                print(f"\n🏆 Top 10 estaciones con más bicicletas:")
                for i, station in enumerate(stations_sorted, 1):
                    station_id = station.get('station_id', 'N/A')
                    bikes = station.get('num_bikes_available', 0)
                    docks = station.get('num_docks_available', 0)
                    print(f"{i:2d}. Estación {station_id}: {bikes} bicicletas, {docks} lugares")
        else:
            print("⚠️  No se pudo obtener el estado actual de las estaciones")
    
    def mostrar_subte_status(self):
        """Muestra el estado de las líneas de subte"""
        print("\n🚇 ESTADO DEL SUBTE")
        print("-" * 25)
        
        print("Obteniendo estado de líneas...")
        subte_data = self.realtime.get_subte_status()
        
        if not subte_data:
            print("❌ No se pudo obtener información del subte")
            print("🔗 Intenta acceder directamente a: https://api-transporte.buenosaires.gob.ar")
            return
        
        # Procesar alertas de servicio
        alerts = subte_data.get('entity', [])
        if alerts:
            print(f"\n📢 Alertas activas ({len(alerts)}):")
            for i, alert in enumerate(alerts[:5], 1):  # Mostrar primeras 5
                alert_info = alert.get('alert', {})
                description = alert_info.get('description_text', {}).get('translation', [])
                if description:
                    text = description[0].get('text', 'Sin descripción')
                    print(f"{i}. {text[:100]}...")
        else:
            print("✅ No hay alertas activas en el sistema de subte")
            print("🚇 Todas las líneas funcionan con normalidad")
    
    def mostrar_colectivos_info(self):
        """Muestra información de colectivos"""
        print("\n🚌 INFORMACIÓN DE COLECTIVOS")
        print("-" * 35)
        
        print("⚠️  La API de colectivos requiere permisos especiales")
        print("🔗 Para acceso completo, consulta: https://api-transporte.buenosaires.gob.ar")
        print("\n📋 Funcionalidades disponibles en la API oficial:")
        print("   • Posición en tiempo real de colectivos")
        print("   • Tiempo de arribo a paradas")
        print("   • Rutas y recorridos")
        print("   • Alertas de servicio")
    
    def mostrar_estado_transito(self):
        """Muestra el estado del tránsito y cortes"""
        print("\n🚦 ESTADO DEL TRÁNSITO")
        print("-" * 30)
        
        print("Obteniendo información de tránsito...")
        traffic_data = self.realtime.get_traffic_info()
        
        if not traffic_data:
            print("❌ No se pudo obtener información de tránsito")
            print("🔗 Intenta acceder directamente a: https://api-transporte.buenosaires.gob.ar")
            return
        
        # Procesar cortes de tránsito
        cortes = traffic_data.get('cortes', []) if isinstance(traffic_data, dict) else []
        
        if cortes:
            print(f"\n🚧 Cortes de tránsito activos ({len(cortes)}):")
            for i, corte in enumerate(cortes[:10], 1):  # Mostrar primeros 10
                calle = corte.get('calle', 'N/A')
                motivo = corte.get('motivo', 'Sin especificar')
                desde = corte.get('desde', '')
                hasta = corte.get('hasta', '')
                
                print(f"{i:2d}. 📍 {calle}")
                if desde or hasta:
                    print(f"     🔄 Desde: {desde} - Hasta: {hasta}")
                print(f"     📝 Motivo: {motivo}")
        else:
            print("✅ No hay cortes de tránsito reportados")
            print("🚗 El tráfico fluye con normalidad")
    
    def mostrar_calidad_aire(self):
        """Muestra la calidad del aire actual"""
        print("\n🌫️ CALIDAD DEL AIRE")
        print("-" * 25)
        
        print("Obteniendo datos de calidad del aire...")
        air_data = self.realtime.get_air_quality()
        
        if not air_data:
            print("❌ No se pudo obtener información de calidad del aire")
            print("🔗 Consulta directamente: https://aqicn.org/city/buenos-aires/es/")
            return
        
        if air_data.get('status') == 'ok':
            data = air_data.get('data', {})
            aqi = data.get('aqi', 'N/A')
            
            # Interpretar nivel AQI
            if isinstance(aqi, int):
                if aqi <= 50:
                    nivel = "🟢 Bueno"
                elif aqi <= 100:
                    nivel = "🟡 Moderado" 
                elif aqi <= 150:
                    nivel = "🟠 Dañino para grupos sensibles"
                elif aqi <= 200:
                    nivel = "🔴 Dañino"
                else:
                    nivel = "🟣 Muy dañino"
            else:
                nivel = "⚪ No disponible"
            
            print(f"\n📊 Índice de Calidad del Aire (AQI): {aqi}")
            print(f"📈 Nivel: {nivel}")
            
            # Mostrar contaminantes específicos
            iaqi = data.get('iaqi', {})
            if iaqi:
                print(f"\n🧪 Contaminantes específicos:")
                for contaminant, value in iaqi.items():
                    if isinstance(value, dict) and 'v' in value:
                        print(f"   {contaminant.upper()}: {value['v']}")
            
            # Mostrar estación de medición
            city = data.get('city', {}).get('name', 'Buenos Aires')
            time = data.get('time', {}).get('s', 'N/A')
            print(f"\n📍 Estación: {city}")
            print(f"🕐 Última actualización: {time}")
        else:
            print("⚠️  Usando datos de demostración")
            print("📊 AQI estimado: 45-65 (Bueno a Moderado)")
            print("🌱 Recomendación: Actividades al aire libre son seguras")
    
    def mostrar_datos_meteorologicos(self):
        """Muestra datos meteorológicos actuales"""
        print("\n🌤️ DATOS METEOROLÓGICOS")
        print("-" * 30)
        
        print("Obteniendo datos meteorológicos...")
        weather_data = self.realtime.get_weather_data()
        
        if weather_data and weather_data.get('status') == 'demo':
            demo_data = weather_data.get('demo_data', {})
            print(f"\n⚠️  {weather_data.get('message')}")
            print(f"\n📊 Datos de demostración:")
            print(f"🌡️  Temperatura: {demo_data.get('temperature', 'N/A')}")
            print(f"💧 Humedad: {demo_data.get('humidity', 'N/A')}")
            print(f"☁️  Descripción: {demo_data.get('description', 'N/A')}")
            
            print(f"\n🔗 Para datos meteorológicos precisos:")
            print(f"   • Servicio Meteorológico Nacional: https://www.smn.gob.ar/")
            print(f"   • Weather API: https://openweathermap.org/api")
        else:
            print("❌ No se pudieron obtener datos meteorológicos")
    
    def mostrar_geocodificacion(self):
        """Permite geocodificar direcciones"""
        print("\n📍 GEOCODIFICACIÓN DE DIRECCIONES")
        print("-" * 40)
        
        address = input("Ingresa una dirección en CABA (ej: Corrientes 1000): ").strip()
        
        if not address:
            print("⚠️  Debes ingresar una dirección")
            return
        
        print(f"\nGeocodificando: {address}")
        geo_data = self.realtime.geocode_address(address)
        
        if not geo_data:
            print("❌ No se pudo geocodificar la dirección")
            return
        
        # Procesar respuesta de geocodificación
        if isinstance(geo_data, dict):
            # Estructura puede variar según la API
            direccion = geo_data.get('direccion', address)
            coordenadas = geo_data.get('coordenadas', {})
            
            print(f"\n✅ Dirección normalizada: {direccion}")
            
            if coordenadas:
                lat = coordenadas.get('lat', 'N/A')
                lng = coordenadas.get('lng', 'N/A')
                print(f"🗺️  Coordenadas: {lat}, {lng}")
                
                # Obtener datos útiles por ubicación
                if lat != 'N/A' and lng != 'N/A':
                    try:
                        useful_data = self.realtime.get_useful_data(float(lat), float(lng))
                        if useful_data:
                            self.mostrar_datos_utiles_ubicacion(useful_data)
                    except (ValueError, TypeError):
                        print("⚠️  No se pudieron obtener datos adicionales")
        else:
            print("⚠️  Formato de respuesta inesperado")
    
    def mostrar_servicios_ubicacion(self):
        """Muestra servicios útiles por ubicación"""
        print("\n🗺️ SERVICIOS POR UBICACIÓN")
        print("-" * 35)
        
        print("Opciones de consulta:")
        print("1. Por dirección")
        print("2. Por coordenadas")
        
        try:
            choice = input("\nSelecciona una opción (1-2): ").strip()
            
            if choice == '1':
                address = input("Ingresa dirección: ").strip()
                if address:
                    # Primero geocodificar
                    geo_data = self.realtime.geocode_address(address)
                    if geo_data and isinstance(geo_data, dict):
                        coordenadas = geo_data.get('coordenadas', {})
                        lat = coordenadas.get('lat')
                        lng = coordenadas.get('lng')
                        if lat and lng:
                            useful_data = self.realtime.get_useful_data(float(lat), float(lng))
                            self.mostrar_datos_utiles_ubicacion(useful_data)
                        else:
                            print("❌ No se pudieron obtener coordenadas")
                    else:
                        print("❌ No se pudo geocodificar la dirección")
                        
            elif choice == '2':
                lat_str = input("Latitud: ").strip()
                lng_str = input("Longitud: ").strip()
                
                try:
                    lat = float(lat_str)
                    lng = float(lng_str)
                    useful_data = self.realtime.get_useful_data(lat, lng)
                    self.mostrar_datos_utiles_ubicacion(useful_data)
                except ValueError:
                    print("❌ Coordenadas inválidas")
            else:
                print("⚠️  Opción inválida")
                
        except KeyboardInterrupt:
            return
    
    def mostrar_datos_utiles_ubicacion(self, data: Dict):
        """Muestra datos útiles de una ubicación específica"""
        if not data:
            print("❌ No se pudieron obtener datos de la ubicación")
            return
        
        print(f"\n📍 INFORMACIÓN DE LA UBICACIÓN")
        print("-" * 35)
        
        # La estructura depende de la API específica
        if isinstance(data, dict):
            # Información básica
            barrio = data.get('barrio', 'N/A')
            comuna = data.get('comuna', 'N/A')
            
            print(f"🏘️  Barrio: {barrio}")
            print(f"🏛️  Comuna: {comuna}")
            
            # Servicios
            comisaria = data.get('comisaria', 'N/A')
            hospital = data.get('area_hospitalaria', 'N/A')
            codigo_postal = data.get('codigo_postal', 'N/A')
            
            print(f"👮 Comisaría: {comisaria}")
            print(f"🏥 Área hospitalaria: {hospital}")
            print(f"📬 Código postal: {codigo_postal}")
            
            # Información urbanística
            cpu = data.get('codigo_planeamiento_urbano', 'N/A')
            if cpu != 'N/A':
                print(f"🏗️  Código Planeamiento Urbano: {cpu}")
        else:
            print("⚠️  Datos en formato no esperado")
            print(f"Respuesta: {str(data)[:200]}...")
    
    def ejecutar(self):
        """Ejecuta el programa principal"""
        print("🔄 Inicializando Buenos Aires Data Explorer v2.0...")
        print("📡 Conectando con APIs de datos históricos y tiempo real...")
        
        while True:
            self.mostrar_menu_principal()
            
            try:
                opcion = input("\nSelecciona una opción: ").strip()
                
                if opcion == '0':
                    print("\n👋 ¡Hasta luego!")
                    break
                elif opcion == '1':
                    self.buscar_por_tema()
                elif opcion == '2':
                    self.listar_recientes()
                elif opcion == '3':
                    self.ver_por_organizacion()
                elif opcion == '4':
                    self.ver_detalles_dataset()
                elif opcion == '5':
                    self.descargar_recursos()
                elif opcion == '6':
                    self.mostrar_estadisticas()
                elif opcion == '7':
                    self.mostrar_transporte_publico()
                elif opcion == '8':
                    self.mostrar_estado_transito()
                elif opcion == '9':
                    self.mostrar_calidad_aire()
                elif opcion == '10':
                    self.mostrar_datos_meteorologicos()
                elif opcion == '11':
                    self.mostrar_geocodificacion()
                elif opcion == '12':
                    self.mostrar_servicios_ubicacion()
                else:
                    print("⚠️  Opción inválida. Intenta de nuevo.")
                
                if opcion != '0' and opcion not in ['7']:  # El menú de transporte maneja su propia pausa
                    input("\nPresiona Enter para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                print("Continuando...")
                input("Presiona Enter para continuar...")

def main():
    """Función principal"""
    explorer = MenuExplorer()
    explorer.ejecutar()

if __name__ == "__main__":
    main()
