import pandas as pd

file = 'Ground_Water_Level_MOHALI_2000-01-01_2025-12-31.csv'
df = pd.read_csv(file)
output = 'pivoted_'+file

df['date_parsed'] = pd.to_datetime(df['description'], errors='coerce')

print(f"Failed rows: {df['date_parsed'].isna().sum()}")

df['month_year'] = df['date_parsed'].dt.to_period('M')

metadata_cols = [
    'stationCode', 'stationName', 'stationType', 
    'latitude', 'longitude', 'district', 'state', 
    'tehsil', 'block', 'village', 'unit', 
    'well_type', 'well_depth', 'well_aquifer_type'
]

output_df = pd.pivot_table(
    df,
    index=metadata_cols,
    columns='month_year',
    values='datatype_code',
    aggfunc='mean'
)

output_df.to_csv(output)