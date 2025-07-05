# Valencia Green Areas and Public Transport Accessibility API

This FastAPI application processes geospatial data of Valencia city retrieved from external URLs and stores it in a PostgreSQL database with PostGIS support. The API provides endpoints to analyze and deliver valuable urban indicators by neighborhoods ("barrios") related to green spaces and public transport accessibility.

## Features

- **Data Ingestion:**  
  Fetches geospatial datasets of Valencia from online sources and inserts them into a PostgreSQL/PostGIS database.

- **Green Areas Ratios Endpoint:**  
  Calculates and returns ratios of green area per surface and per inhabitant for each neighborhood.

- **Public Transport Accessibility Endpoint:**  
  Analyzes accessibility to MetroValencia and EMT bus stops by neighborhood, based on a pedestrian walkable graph.  
  - Computes the proportion of walkable graph nodes within each neighborhood that have access to public transport stops within a defined threshold.  
  - Calculates the nearest public transport stop to the centroid of each neighborhood.

- **Combined Indicator Endpoint:**  
  Provides a GeoJSON response with a composite indicator for each neighborhood, combining:  
  - The percentage of accessible walkable nodes  
  - The green area ratio  
  through a linear combination, giving a holistic view of green space and transit accessibility.

## Technologies

- FastAPI for building the API  
- PostgreSQL with PostGIS for spatial database management  
- GeoPandas and NetworkX for geospatial and graph analysis  
- Python libraries such as Shapely, SQLAlchemy, and others for spatial computations  

## Usage

1. Clone the repository  
2. Configure environment variables (database credentials, data URLs, etc.) in a `.env` file (not tracked in Git)  
3. Run the FastAPI app with Uvicorn  
4. Access endpoints to obtain urban indicators by neighborhood

---

This project helps urban planners and researchers evaluate the availability of green spaces and public transport accessibility across Valencia’s neighborhoods, supporting sustainable city development.

