import pandas as pd
from sqlalchemy import create_engine, text

# Connect to our local Docker Postgres
DB_URL = "postgresql://farm_admin:farm_password@127.0.0.1:5434/farm_management"
engine = create_engine(DB_URL)

def process_and_load_fao_data(csv_path):
    print(f"Reading real FAOSTAT data from {csv_path}...")
    df_raw = pd.read_csv(csv_path)

    # Filter for East Africa to keep API calls manageable later
    target_countries = ['Kenya', 'Rwanda', 'Uganda', 'United Republic of Tanzania']
    df_raw = df_raw[df_raw['Area'].isin(target_countries)].copy()

    # Map countries to approximate agricultural centroid coordinates
    coordinates = {
        'Kenya': {'lat': -0.0236, 'lon': 37.9062, 'zone': 'Equatorial'},
        'Rwanda': {'lat': -1.9403, 'lon': 29.8739, 'zone': 'Highland Tropical'},
        'Uganda': {'lat': 1.3733, 'lon': 32.2903, 'zone': 'Tropical'},
        'United Republic of Tanzania': {'lat': -6.3690, 'lon': 34.8888, 'zone': 'Sub-Tropical'}
    }

    df_regions = pd.DataFrame([
        {
            "region_id": f"REG_{str(i+1).zfill(3)}",
            "region_name": country,
            "latitude": coords['lat'],
            "longitude": coords['lon'],
            "climate_zone": coords['zone']
        }
        for i, (country, coords) in enumerate(coordinates.items())
    ])

    unique_crops = df_raw[['Area', 'Item']].drop_duplicates()
    df_fields = unique_crops.merge(df_regions[['region_name', 'region_id']], left_on='Area', right_on='region_name')
    df_fields['field_id'] = [f"FLD_{str(i+1).zfill(3)}" for i in range(len(df_fields))]
    df_fields['field_name'] = df_fields['Area'] + " " + df_fields['Item'] + " Production"
    df_fields['area_hectares'] = 0.0 
    df_fields['soil_type'] = 'Mixed National'

    df_harvests = df_raw.merge(df_fields[['Area', 'Item', 'field_id']], on=['Area', 'Item'])
    df_harvests['yield_kg'] = df_harvests['Value'] * 0.1 # Convert hg/ha to kg/ha
    
    df_harvests = df_harvests[['field_id', 'Item', 'Year', 'yield_kg']].rename(columns={'Item': 'crop_type'})
    df_harvests['planting_date'] = pd.to_datetime(df_harvests['Year'].astype(str) + '-01-01').dt.date
    df_harvests['harvest_date'] = pd.to_datetime(df_harvests['Year'].astype(str) + '-12-31').dt.date
    df_harvests['harvest_id'] = range(100, 100 + len(df_harvests))
    df_harvests['updated_at'] = pd.Timestamp.now()
    df_harvests = df_harvests.drop(columns=['Year'])

    with engine.connect() as conn:
        print("Wiping existing schema...")
        conn.execute(text("DROP TABLE IF EXISTS harvest_yields CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS fields CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS regions CASCADE;"))
        conn.commit()

        print("Loading normalized Kaggle data into Postgres...")
        df_regions[['region_id', 'region_name', 'latitude', 'longitude', 'climate_zone']].to_sql('regions', engine, if_exists='append', index=False)
        df_fields[['field_id', 'region_id', 'field_name', 'area_hectares', 'soil_type']].to_sql('fields', engine, if_exists='append', index=False)
        df_harvests[['harvest_id', 'field_id', 'crop_type', 'planting_date', 'harvest_date', 'yield_kg', 'updated_at']].to_sql('harvest_yields', engine, if_exists='append', index=False)
        
        conn.execute(text("ALTER TABLE regions ADD PRIMARY KEY (region_id);"))
        conn.execute(text("ALTER TABLE fields ADD PRIMARY KEY (field_id);"))
        conn.execute(text("ALTER TABLE harvest_yields ADD PRIMARY KEY (harvest_id);"))
        conn.commit()
        
    print("Real Kaggle dataset successfully normalized and loaded!")

if __name__ == "__main__":
    process_and_load_fao_data("yield.csv")
