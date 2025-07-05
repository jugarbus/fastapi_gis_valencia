from app.utils.helpers import (load_admin_data, load_green_spaces, compute_green_area_ratio,
                               merge_population, compute_green_area_per_capita, load_population_csv)



def get_green_gdf():

    admin_barr = load_admin_data()
    gdf_green = load_green_spaces()
    df_pop_barr = load_population_csv()
    admin_barr_green = compute_green_area_ratio(admin_barr, gdf_green)
    gdf_green_pop_barr_0 = merge_population(admin_barr_green, df_pop_barr)
    gdf_green_pop_barr = compute_green_area_per_capita(gdf_green_pop_barr_0)

    return gdf_green_pop_barr




if __name__ == '__main__':

    # Cargar los datos de los barrios
    admin_barr = load_admin_data()
    print(admin_barr.crs)

    # Cargar los datos de las áreas verdes
    gdf_green = load_green_spaces()
    print(gdf_green.crs)

    # Cargar datos de población de barrios
    df_pop_barr = load_population_csv()

    # Calcular el área de los barrios y la intersección con las áreas verdes y unir la información de la zona verde a los barrios
    admin_barr_green = compute_green_area_ratio(admin_barr, gdf_green)
    print(admin_barr_green.crs)


    # Unir la población a los barrios y calcular el área verde per cápita
    gdf_green_pop_barr_0 = merge_population(admin_barr_green, df_pop_barr)
    print(gdf_green_pop_barr_0.crs)

    gdf_green_pop_barr = compute_green_area_per_capita(gdf_green_pop_barr_0)
    print(gdf_green_pop_barr.crs)


    print(gdf_green_pop_barr.columns)
