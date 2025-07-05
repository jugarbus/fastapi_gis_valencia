import os
from dotenv import load_dotenv
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from app.utils.helpers import *
from app.api.green_area import get_green_gdf
from pydantic import BaseModel
from typing import Optional
import numpy as np
from fastapi.responses import JSONResponse
from shapely.geometry import mapping
import orjson
import uvicorn


# Conectar con base de datos a partir de .env
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Cargar geojson accesibility de la base de datos
query = "SELECT * FROM barrios_accesibilidad;"
acces_gdf = gpd.read_postgis(query, con=engine, geom_col='geometry')
acces_gdf[acces_gdf.select_dtypes(include=['object']).columns] = acces_gdf[acces_gdf.select_dtypes(include=['object']).columns].fillna("Desconocido")
acces_gdf[acces_gdf.select_dtypes(include=['float64']).columns] = acces_gdf[acces_gdf.select_dtypes(include=['float64']).columns].fillna(0)

# Cargar geojson green
green_gdf = get_green_gdf()
green_gdf[green_gdf.select_dtypes(include=['object']).columns] = green_gdf[green_gdf.select_dtypes(include=['object']).columns].fillna("Desconocido")
green_gdf[green_gdf.select_dtypes(include=['float64']).columns] = green_gdf[green_gdf.select_dtypes(include=['float64']).columns].fillna(0)



def create_indicator(gdf, alpha, beta):
    gdf['icvu'] = alpha * gdf['green_ratio'] + beta * (gdf['accessibility_percentage']/100)
    return gdf


# Define el modelo para la respuesta de zonas verdes
class Verde(BaseModel):
    coddistbar: int
    nombre: str
    green_area_m2: Optional[float]
    green_ratio: Optional[float]
    barr_area_imputed: float
    green_area_per_capita_m2: Optional[float]
    population: float


class Acces(BaseModel):
    coddistbar: int
    nombre: str
    centroid_distance: Optional[float]
    centroid_estimated_time: Optional[float]
    centroid_route_type: Optional[str]
    num_stops: Optional[float]
    accessibility_percentage: Optional[float]


app = FastAPI()


@app.get("/zonas-verdes/coord", response_model=Verde, tags=["Zonas Verdes"])
def zona_verde_coord(lon: float = Query(...), lat: float = Query(...)):

    barrio_id = get_barr_id_coords(lon, lat, green_gdf)

    print(f"barrio_id calculado: {barrio_id}")


    if not barrio_id:
        raise HTTPException(status_code=404, detail="Coordenadas fuera de los límites de Valencia")

    barrio_data = green_gdf.loc[green_gdf['coddistbar'] == barrio_id]


    if not barrio_data.empty:

        barrio = barrio_data.iloc[0]

        verde = Verde(
            coddistbar=barrio["coddistbar"],
            nombre=barrio["nombre"],
            green_area_m2=barrio["green_area_m2"],
            green_ratio=barrio["green_ratio"],
            barr_area_imputed=barrio["barr_area_imputed"],
            green_area_per_capita_m2=barrio["green_area_per_capita_m2"],
            population=barrio["population"],
        )
        return verde
    else:
        raise HTTPException(status_code=404, detail="Barrio no encontrado")


@app.get("/accesibilidad/coord", response_model=Acces, tags=["Accesibilidad"])
def acces_coord(lon: float = Query(...), lat: float = Query(...)):

    barrio_id = get_barr_id_coords(lon, lat, acces_gdf)

    if not barrio_id:
        raise HTTPException(status_code=404, detail="Coordenadas fuera de los límites de Valencia")

    barrio_data = acces_gdf.loc[acces_gdf['coddistbar'] == barrio_id]

    if not barrio_data.empty:

        barrio = barrio_data.iloc[0]

        acces = Acces(
            coddistbar=barrio["coddistbar"],
            nombre=barrio["nombre"],
            centroid_distance=barrio["centroid_distance"],
            centroid_estimated_time=barrio["centroid_estimated_time"],
            centroid_route_type=barrio["centroid_route_type"],
            num_stops=barrio["num_stops"],
            accessibility_percentage=barrio["accessibility_percentage"],
        )
        return acces
    else:
        raise HTTPException(status_code=404, detail="Barrio no encontrado")




@app.get("/ICVU/heatmap", tags=["ICVU"])
def get_heatmap(alpha: float = Query(0.7), beta: float = Query(0.5)):
    merged_gdf = acces_gdf.merge(green_gdf, on='coddistbar', suffixes=('_acceso', '_verde'))
    merged_gdf = create_indicator(merged_gdf, alpha, beta)

    geojson_data = merged_gdf[['coddistbar', 'nombre_acceso', 'icvu', 'geometry_verde']].copy()
    geojson_data = geojson_data.rename(columns={'geometry_verde': 'geometry'})
    geojson_data = geojson_data[geojson_data['geometry'].notnull() & geojson_data['geometry'].apply(lambda x: x.is_valid)]

    features = []
    for _, row in geojson_data.iterrows():
        feature = {
            "type": "Feature",
            "geometry": mapping(row['geometry']),
            "properties": {
                "coddistbar": row['coddistbar'],
                "nombre_acceso": row['nombre_acceso'],
                "icvu": row['icvu']
            }
        }
        features.append(feature)

    return JSONResponse(content={
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features
    })


if __name__ == "__main__":    # Use this for debugging purposes only

    uvicorn.run(app="main:app", host="0.0.0.0", port=9000, reload=True)