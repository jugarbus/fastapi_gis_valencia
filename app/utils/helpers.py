import re
import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox # depende internamente de GeoPandas
import networkx as nx
import unicodedata
import os
import shutil
import pandas as pd
from shapely.geometry import Point
from collections import Counter
from sqlalchemy import create_engine
from dotenv import load_dotenv
import requests
import zipfile
from geopy.distance import geodesic


## ZONAS VERDES ##

# Cargar los datos de los distritos y barrios
def load_admin_data():

    url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/barris-barrios/exports/geojson?lang=es&timezone=Europe%2FBerlin"
    admin_barr = gpd.read_file(url)
    admin_barr.loc[admin_barr['nombre'] == 'MAHUELLA-TAULADELLA', 'coddistbar'] = 1234 # Cambiar el valor de 'coddistbar' para el barrio 'MAHUELLA-TAULADELLA'
    admin_barr['coddistbar'] = admin_barr['coddistbar'].astype(int)

    return admin_barr


# Cargar los datos de las áreas verdes
def load_green_spaces():
    url = "https://valencia.opendatasoft.com/api/explore/v2.1/catalog/datasets/espais-verds-espacios-verdes/exports/geojson?lang=es&timezone=Europe%2FBerlin"
    gdf_green = gpd.read_file(url)
    return gdf_green


def load_population_csv_local():
    df_pop_barr = pd.read_csv('data/020101_PadronBarrios.csv')

    return df_pop_barr

# Cargar datos de población de barrios
def load_population_csv():
    load_dotenv()
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(db_url)
    df_pop_barr = pd.read_sql("SELECT * FROM population_barr", engine)
    df_pop_barr.loc[df_pop_barr['nombre_barrio'] == 'MAUELLA', 'coddistbar'] = 1234

    new_row = pd.DataFrame({'coddistbar': [175], 'nombre_barrio': ['RAFALELL-VISTABELLA'], 'population': [59]})
    df_pop_barr = pd.concat([df_pop_barr, new_row], ignore_index=True)

    return df_pop_barr


# Calcular el área de los barrios y la intersección con las áreas verdes
def compute_green_area_ratio(admin_barr, gdf_green):

    admin_barr_2 = admin_barr.to_crs('EPSG:25830')
    gdf_green_2 = gdf_green.to_crs('EPSG:25830')

    admin_barr_2['barr_area_imputed'] = admin_barr_2.geometry.area

    gdf_inter_barr = gpd.overlay(gdf_green_2, admin_barr_2, how='intersection')

    if 'coddistbar_2' in gdf_inter_barr.columns:
        gdf_inter_barr = gdf_inter_barr.rename(columns={'coddistbar_2': 'coddistbar'})

    gdf_inter_barr['green_area_m2'] = gdf_inter_barr.geometry.area

    gdf_green_barr_0 = gdf_inter_barr.groupby('coddistbar')['green_area_m2'].sum().reset_index()

    # Unir la información de la zona verde a los barrios
    admin_barr_green = admin_barr_2.merge(gdf_green_barr_0, on='coddistbar', how='left')
    admin_barr_green['green_ratio'] = admin_barr_green['green_area_m2'] / admin_barr_green['barr_area_imputed']

    admin_barr_green = admin_barr_green.to_crs("EPSG:4326")


    return admin_barr_green


# Unir la población a los barrios
def merge_population(admin_barr_green, df_pop_barr):

    valores_admin_barr = set(admin_barr_green['coddistbar'].unique())
    valores_df_pop_barrr = set(df_pop_barr['coddistbar'].unique())

    if valores_admin_barr == valores_df_pop_barrr:

        gdf_green_pop_barr_0 = admin_barr_green.merge(df_pop_barr, on='coddistbar', how='inner')
    else:
        raise ValueError("Las columnas 'coddistbar' de los barrios y la población contienen valores únicos diferentes.")

    return gdf_green_pop_barr_0


# Calcular el área verde per cápita
def compute_green_area_per_capita(gdf_green_pop_barr):

    gdf_green_pop_barr['green_area_per_capita_m2'] = gdf_green_pop_barr['green_area_m2'] / gdf_green_pop_barr['population']

    return gdf_green_pop_barr



## ACCESIBILIDAD ##





def download_GTFS(zip_url, zip_filename, folder_extract):
    """
    Descarga y extrae un archivo ZIP con los datos GTFS del metro.

    Parámetros:
    - zip_url (str): URL desde donde se descarga el archivo ZIP.
    - zip_filename (str): Nombre del archivo ZIP que se descargará.
    - folder_extract (str): Carpeta dentro de 'data' donde se extraerán los archivos del ZIP.
    """

    data_folder = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_folder, exist_ok=True)
    path_extract = os.path.join(data_folder, folder_extract)
    response = requests.get(zip_url)

    if response.status_code == 200:

        if os.path.exists(path_extract):
            shutil.rmtree(path_extract)

        os.makedirs(path_extract, exist_ok=True)
        zip_path = os.path.join(data_folder, zip_filename)

        with open(zip_path, 'wb') as f:
            f.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(path_extract)

        print(f"Archivos descargados y extraídos correctamente en {path_extract}.")
    else:
        print(f"Error al descargar el archivo. Código de estado: {response.status_code}")


# Función para cargar los datos de las paradas de metro y bus
def load_transport_stops():
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    df_stops_emt = pd.read_csv(os.path.join(data_folder, 'emt', 'stops.txt'))
    df_stops_metro = pd.read_csv(os.path.join(data_folder, 'metro', 'stops.txt'))

    geometry_bus = [Point(xy) for xy in zip(df_stops_emt['stop_lon'], df_stops_emt['stop_lat'])]
    df_stops_emt = gpd.GeoDataFrame(df_stops_emt, geometry=geometry_bus)
    df_stops_emt.crs = 'EPSG:4326'

    geometry_metro = [Point(xy) for xy in zip(df_stops_metro['stop_lon'], df_stops_metro['stop_lat'])]
    df_stops_metro = gpd.GeoDataFrame(df_stops_metro, geometry=geometry_metro)
    df_stops_metro.crs = 'EPSG:4326'

    return df_stops_emt, df_stops_metro


# Función para unir los datos de EMT con Metro y obtener las paradas comunes
def merge_emt_metro(df_stops_emt, df_stops_metro):
    df_stops_emt['type'] = 'EMT'
    df_stops_metro['type'] = 'MetroValencia'

    df_stops = pd.concat([df_stops_emt, df_stops_metro], ignore_index=True)

    geometry = [Point(xy) for xy in zip(df_stops['stop_lon'], df_stops['stop_lat'])]
    gdf_stops = gpd.GeoDataFrame(df_stops, geometry=geometry)
    gdf_stops.crs = 'EPSG:4326'

    return gdf_stops


def load_transport_route(gdf_stops):
    """
    Carga y combina información de rutas de transporte público (MetroValencia y EMT),
    asociando cada parada con su tipo de transporte (bus, metro, tranvía, etc.).

    Args:
    gdf_stops (gpd.GeoDataFrame): GeoDataFrame con las paradas de transporte, incluyendo columnas
    'stop_id', 'stop_name' y 'geometry'.

    Returns:
    gpd.GeoDataFrame: GeoDataFrame enriquecido con el tipo de ruta ('route_type_en') y el tipo de red ('type').
    """

    map_simple = {0: 'Tram',
                  1: 'Subway',
                  2: 'Railway',
                  3: 'Bus',
                  4: 'Ferry',
                  11: 'Trolleybus',
                  100: 'Railway',
                  109: 'Railway',
                  400: 'Railway',
                  401: 'Subway',
                  700: 'Bus',
                  717: 'Bus',
                  900: 'Tram',
                  1000: 'Ferry', }

    # CARGA A PARTIR DE FICHEROS
    data_folder = os.path.join(os.path.dirname(__file__), 'data')

    df_route_metro = pd.read_csv(os.path.join(data_folder, 'metro', 'routes.txt'))
    df_route_emt = pd.read_csv(os.path.join(data_folder, 'emt', 'routes.txt'))

    df_stop_times_metro = pd.read_csv(os.path.join(data_folder, 'metro', 'stop_times.txt'))
    df_trips_metro = pd.read_csv(os.path.join(data_folder, 'metro', 'trips.txt'))

    df_stop_times_emt = pd.read_csv(os.path.join(data_folder, 'emt', 'stop_times.txt'))
    df_trips_emt = pd.read_csv(os.path.join(data_folder, 'emt', 'trips.txt'))
    # CARGA A PARTIR DE FICHEROS


    # Procesar Metro
    df_route_metro['route_type'] = df_route_metro['route_type'].astype(int)
    df_route_metro['route_type_en'] = df_route_metro['route_type'].map(map_simple)
    df_merged_metro = df_route_metro[['route_type_en', 'route_id']].merge(df_trips_metro[['route_id', 'trip_id']], left_on='route_id', right_on='route_id')[['trip_id', 'route_type_en']].drop_duplicates()
    df_merged_metro = df_merged_metro.merge(df_stop_times_metro, left_on='trip_id', right_on='trip_id')[['route_type_en', 'stop_id']].drop_duplicates()
    df_merged_metro = gdf_stops.merge(df_merged_metro, left_on='stop_id', right_on='stop_id')[['stop_id', 'stop_name', 'route_type_en', 'geometry']].drop_duplicates()
    df_merged_metro['type'] = 'MetroValencia'

    # Procesar EMT
    df_route_emt['route_type'] = df_route_emt['route_type'].astype(int)
    df_route_emt['route_type_en'] = df_route_emt['route_type'].map(map_simple)
    df_merged_emt = df_route_emt[['route_type_en', 'route_id']].merge(df_trips_emt[['route_id', 'trip_id']], left_on='route_id', right_on='route_id')[['trip_id', 'route_type_en']].drop_duplicates()
    df_merged_emt = df_merged_emt.merge(df_stop_times_emt, left_on='trip_id', right_on='trip_id')[['route_type_en', 'stop_id']].drop_duplicates()
    df_merged_emt = gdf_stops.merge(df_merged_emt, left_on='stop_id', right_on='stop_id')[['stop_id', 'stop_name', 'route_type_en', 'geometry']].drop_duplicates()
    df_merged_emt['type'] = 'EMT'

    gdf_combined  = pd.concat([df_merged_emt, df_merged_metro], ignore_index=True)

    return gdf_combined  # ['stop_id', 'stop_name', 'route_type_en', 'geometry', 'type'], dtype='object')


# Función para mostrar el gráfico de tipos de transporte
def plot_transport_modes(df_route_emt, df_route_metro):
    df_route = pd.concat([df_route_metro, df_route_emt], ignore_index=True)

    d = dict(Counter(df_route['route_type_en']))

    transport_colors = {'Metro': '#A65C47',
                        'Bus': '#0BB3D9',
                        'Tram': '#F2B705',
                        'Ferry': '#997CA6',
                        'Trolleybus': '#D91818',
                        'Subway': '#0869A6'}

    f, ax = plt.subplots(1, 1, figsize=(8, 6))

    labels = d.keys()
    values = d.values()
    colors = [transport_colors[l] for l in labels]

    ax.bar(labels, values, color=colors)
    ax.set_xticklabels(labels, fontsize=10, rotation=60, ha='right')

    ax.set_title('Transporte público en Valencia', fontsize=26)
    ax.set_ylabel('Número de rutas', fontsize=15)
    ax.set_yscale('log')

    plt.tight_layout()
    plt.show()

# Función para encontrar el nodo más cercano a las coordenadas (lat, lon)
def find_nearest_node(G, lat, lon):
    return ox.distance.nearest_nodes(G, X=lon, Y=lat)

# Función para calcular la distancia más corta entre dos nodos
def shortest_path_length(G, node1, node2):
    return nx.shortest_path_length(G, node1, node2, weight='length')




# def get_accesibility_gdf(admin_barr, gdf_stops):
#
#     # Definir una velocidad promedio de caminata (en metros por segundo)
#     average_speed = 1.5  # metros por segundo
#     threshold_distance = 500
#
#     for index, row in admin_barr.iterrows():
#         barrio_name = row['nombre']
#
#         if row.geometry is None or row.geometry.is_empty:
#             print(f"Geometría vacía en el barrio: {barrio_name}")
#             continue
#
#         try:
#             # Obtener grafo solo dentro del polígono del barrio
#             G = ox.graph_from_polygon(row.geometry, network_type='walk', simplify=True)
#
#             barrio_center = row.geometry.centroid
#             barr_node = find_nearest_node(G, barrio_center.y, barrio_center.x)
#
#             # Filtrar paradas dentro del barrio
#             nearby_stops = gdf_stops[gdf_stops.geometry.within(row.geometry)]
#
#             # Número de paradas dentro del barrio
#             num_stops = len(nearby_stops)
#
#             min_distance = float('inf')
#             closest_stop = None
#             route_type = None
#
#
#             for stop in nearby_stops.geometry:
#                 try:
#                     stop_node = find_nearest_node(G, stop.y, stop.x)
#                     distance = shortest_path_length(G, barr_node, stop_node)
#
#                     if distance < min_distance:
#                         min_distance = distance
#                         closest_stop = stop
#
#                         # Extraer el tipo de transporte de la parada más cercana
#                         route_type = nearby_stops.loc[nearby_stops.geometry == stop, 'route_type_en'].values[0]
#
#                 except nx.NetworkXNoPath:
#                     continue  # Ignora si no hay camino
#
#
#             estimated_time = min_distance / average_speed if min_distance != float('inf') else None
#
#
#             admin_barr.loc[index, 'accessibility'] = min_distance if min_distance != float('inf') else None
#             admin_barr.loc[index, 'closest_stop'] = closest_stop
#             admin_barr.loc[index, 'route_type'] = route_type
#             admin_barr.loc[index, 'num_stops'] = num_stops
#             admin_barr.loc[index, 'estimated_time'] = estimated_time
#
#
#
#             print(f"Barrio: {barrio_name}")
#             print(f"Centroide: {barrio_center}")
#             print(f"Parada más cercana: {closest_stop}")
#             print(f"Tipo de transporte: {route_type}")
#             print(f"Distancia mínima: {min_distance:.2f} metros" if min_distance != float('inf') else "Sin conexión posible")
#             print(f"Número de paradas dentro del barrio: {num_stops}")
#             print(f"Tiempo estimado: {estimated_time:.2f} segundos" if estimated_time else "Tiempo estimado no disponible")
#             print("-" * 40)
#
#         except Exception as e:
#             print(f"Error procesando el barrio {barrio_name}: {e}")
#
#     return admin_barr



def get_barr_id_coords(lon: float, lat: float, green_gdf: gpd.GeoDataFrame) -> str | None:
    """
    Función para main.py que obtiene el barrio correspondiente a unas coordenadas (lat, lon) dentro de un GeoDataFrame.


    :param lon: Longitud del punto.
    :param lat: Latitud del punto.
    :param green_gdf: GeoDataFrame que contiene los barrios y sus geometrías.
    :return: El nombre del barrio si el punto está dentro de algún barrio, o None si no está dentro de ningún barrio.
    """

    punto = Point(lon, lat)


    if 'geometry' not in green_gdf.columns:
        raise ValueError("El GeoDataFrame no tiene una columna de geometría.")


    result = green_gdf[green_gdf.geometry.contains(punto)]

    if not result.empty:
        return result.iloc[0]["coddistbar"]
    return None






def get_accesibility_gdf(admin_barr, gdf_stops, threshold_distance = 300, average_speed = 1.5):

    for index, row in admin_barr.iterrows():
        barrio_name = row['nombre']

        if row.geometry is None or row.geometry.is_empty:
            print(f"Geometría vacía en el barrio: {barrio_name}")
            continue

        try:

            G = ox.graph_from_polygon(row.geometry, network_type='walk', simplify=True)

            barr_centroid = row.geometry.centroid
            barr_node = find_nearest_node(G, barr_centroid.y, barr_centroid.x)

            nearby_stops = gdf_stops[gdf_stops.geometry.within(row.geometry)]

            num_stops = len(nearby_stops)

            # Inicialización para obtener parada cerca del centroide
            min_distance = float('inf')
            closest_stop = None
            route_type = None

            # Inicializar el conjunto de nodos accesibles
            accessible_nodes_set = set()
            total_nodes = len(G.nodes)

            # Guardar las distancias de las paradas a los nodos
            for stop in nearby_stops.geometry:
                try:
                    stop_node = find_nearest_node(G, stop.y, stop.x)
                    distance_center = shortest_path_length(G, barr_node, stop_node)

                    # Actualizar la parada más cercana
                    if distance_center < min_distance:
                        min_distance = distance_center
                        closest_stop = stop
                        route_type = nearby_stops.loc[nearby_stops.geometry == stop, 'route_type_en'].values[0]

                    # Calcular accesibilidad para cada nodo
                    for node in G.nodes:
                        distance = shortest_path_length(G, node, stop_node)

                        if distance <= threshold_distance:
                            accessible_nodes_set.add(node)

                except nx.NetworkXNoPath:
                    continue

            # Cálculo del porcentaje de nodos accesibles
            accessible_nodes = len(accessible_nodes_set)
            accessibility_percentage = (accessible_nodes / total_nodes) * 100 if total_nodes > 0 else None

            # Estimar el tiempo de caminata hacia la parada más cercana
            estimated_time = min_distance / average_speed if min_distance != float('inf') else None

            admin_barr.loc[index, 'centroid_distance'] = min_distance if min_distance != float('inf') else None
            admin_barr.loc[index, 'centroid_estimated_time'] = estimated_time
            admin_barr.loc[index, 'centroid_closest_stop'] = closest_stop
            admin_barr.loc[index, 'centroid_route_type'] = route_type
            admin_barr.loc[index, 'num_stops'] = num_stops
            admin_barr.loc[index, 'accessibility_percentage'] = accessibility_percentage

            print(f"Barrio: {barrio_name}")
            print(f"Centroide: {row.geometry.centroid}")
            print(f"Parada más cercana: {closest_stop}")
            print(f"Tipo de transporte: {route_type}")
            print(f"Distancia mínima: {min_distance:.2f} metros" if min_distance != float('inf') else "Sin conexión posible")
            print(f"Número de paradas dentro del barrio: {num_stops}")
            print(f"Tiempo estimado: {estimated_time:.2f} segundos" if estimated_time else "Tiempo estimado no disponible")
            print(f"Porcentaje de nodos accesibles a <300m: {accessibility_percentage:.2f}%")
            print("-" * 40)

        except Exception as e:
            print(f"Error procesando el barrio {barrio_name}: {e}")

    return admin_barr


