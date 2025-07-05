from dotenv import load_dotenv
import psycopg2
from sqlalchemy import create_engine
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
import geopandas as gpd
import os

from sqlalchemy import create_engine
from app.utils.helpers import (load_admin_data, load_population_csv_local, load_green_spaces, compute_green_area_ratio,
                               merge_population, compute_green_area_per_capita)

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las variables de entorno
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construir la URL de conexión a la base de datos
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear la conexión a PostgreSQL
engine = create_engine(DATABASE_URL)


# # Cargar el archivo csv
# df_pop_barr = load_population_csv_local()
# print(df_pop_barr)
#
#
# # Insertar en la base de datos
# df_pop_barr.to_sql("population_barr", engine, if_exists="replace", index=False)



# Insertar geodataframe

file_path = os.path.join(os.path.dirname(__file__), 'data', 'acces_admin_barr_previous.geojson')

# Leer el archivo GeoJSON con GeoPandas
acces_admin_barr = gpd.read_file(file_path)
# Verifica el contenido del GeoDataFrame (opcional)
print(acces_admin_barr)


# Insertar el GeoDataFrame en PostgreSQL
acces_admin_barr.to_postgis(name='barrios_accesibilidad', con=engine, if_exists='replace')

print("GeoDataFrame insertado en la base de datos correctamente.")


