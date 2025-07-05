import os
import pandas as pd
import re

# Función para extraer el nombre del barrio
def extract_barrio_name(text):
    # Usamos una expresión regular para encontrar las palabras después del último punto.
    match = re.search(r'([^.]+$)', text)
    if match:
        return match.group(1).strip()
    return None

# Función para extraer la población bajo el año 2024
def extract_population(df):
    population = None
    # Iterar sobre todas las celdas del DataFrame
    for row in range(df.shape[0]):
        for col in range(df.shape[1]):
            # Buscar el año 2024 en el DataFrame
            if df.iloc[row, col] == 2024:
                # Extraer el valor debajo de 2024
                if row + 1 < df.shape[0]:
                    population = df.iloc[row + 1, col]
                break
        if population is not None:
            break
    return population

# Ruta de los archivos Excel
path = 'barrios'

# Listar todos los archivos .xlsx en el directorio
excel_files = [f for f in os.listdir(path) if f.endswith('.xlsx')]

# Crear listas para almacenar los resultados
barrio_names = []
populations = []

# Iterar sobre todos los archivos Excel
for file in excel_files:
    # Leer el archivo Excel
    file_path = os.path.join(path, file)
    df = pd.read_excel(file_path, engine='openpyxl')

    # Extraer el nombre del barrio de la celda 2 (en la primera columna) y limpiar el texto
    barrio_name = extract_barrio_name(str(df.iloc[1, 0]))  # Fila 2, columna 1
    barrio_names.append(barrio_name)

    # Extraer la población buscando el valor 2024
    population = extract_population(df)
    populations.append(population)

# Crear un DataFrame con los resultados
result_df = pd.DataFrame({
    'nombre_barrio': barrio_names,
    'population': populations
})



print("Proceso completado. Los datos se han guardado en '020101_PadronBarrios.csv'.")

result_df['nombre_barrio'] = result_df['nombre_barrio'].apply(lambda x: x.upper())
# Guardar los resultados en un archivo CSV
result_df.to_csv('data/020101_PadronBarrios.csv', index=False)