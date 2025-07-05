from app.utils.helpers import (load_admin_data, get_accesibility_gdf, load_transport_stops, download_GTFS, merge_emt_metro, load_transport_route)
import os


if __name__ == '__main__':


    # Descarga de los datos de Metro Valencia
    zip_url_1 = "https://files.mobilitydatabase.org/mdb-1054/mdb-1054-202506120405/mdb-1054-202506120405.zip"
    zip_filename_1 = 'mdb-1054.zip'
    folder_1 = 'metro'
    download_GTFS(zip_url_1, zip_filename_1, folder_1)

    # Definir las rutas y parámetros para los datos de la EMT
    zip_url_2 = "https://files.mobilitydatabase.org/mdb-795/mdb-795-202506110231/mdb-795-202506110231.zip"
    zip_filename_2 = 'mdb-795.zip'
    folder_2 = 'emt'
    download_GTFS(zip_url_2, zip_filename_2, folder_2)

    # Cargar datos de las paradas de metro y bus
    df_stops_emt, df_stops_metro = load_transport_stops()
    print(df_stops_emt.crs)
    print(df_stops_metro.crs)


    # Unir los datos de EMT con Metro
    gdf_stops = merge_emt_metro(df_stops_emt,df_stops_metro)
    print(gdf_stops.crs)

    gdf_stops = load_transport_route(gdf_stops)
    print(gdf_stops.crs)

    # Cargar los datos administrativos de los barrios de Valencia
    admin_barr = load_admin_data()
    print(admin_barr.crs)


    acces_admin_barr = get_accesibility_gdf(admin_barr,gdf_stops)
    print(admin_barr.crs)

    base_dir = os.path.dirname(__file__)
    output_path = os.path.abspath(os.path.join(base_dir, "../utils/data/acces_admin_barr_previous.geojson"))
    acces_admin_barr.to_file(output_path, driver="GeoJSON")