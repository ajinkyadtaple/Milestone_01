import pandas as pd
from datasets import load_dataset
from src.config import CLEANED_DATA_PATH

def clean_rating(val):
    if not val or not isinstance(val, str):
        return 0.0
    val = val.strip()
    if '/' in val:
        parts = val.split('/')
        try:
            return float(parts[0].strip())
        except ValueError:
            return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

def clean_cost(val):
    if not val or not isinstance(val, str):
        return None
    val = val.replace(',', '').strip()
    try:
        return int(val)
    except ValueError:
        return None

def run_ingestion():
    print("Ingestion starting: Fetching dataset from Hugging Face...")
    try:
        dataset = load_dataset("ManikaSaini/zomato-restaurant-recommendation")
        df = dataset['train'].to_pandas()
        print(f"Downloaded raw dataset with shape: {df.shape}")

        print("Cleaning data fields...")
        # 1. Clean rating
        df['rate_float'] = df['rate'].apply(clean_rating)
        
        # 2. Clean cost for two people
        df['cost_clean'] = df['approx_cost(for two people)'].apply(clean_cost)
        
        # Fill missing costs with median cost
        median_cost = df['cost_clean'].median()
        if pd.isna(median_cost):
            median_cost = 500  # Default fallback if all are NaN
        df['cost_clean'] = df['cost_clean'].fillna(median_cost).astype(int)

        # 3. Clean votes
        df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0).astype(int)

        # 4. Standardise search terms (lowercase, stripped)
        df['location_clean'] = df['location'].fillna("").astype(str).str.strip().str.lower()
        df['cuisines_clean'] = df['cuisines'].fillna("").astype(str).str.strip().str.lower()

        # 5. Clean name
        df['name'] = df['name'].fillna("Unknown Restaurant").astype(str).str.strip()

        # Keep relevant columns to optimize footprint
        cols_to_keep = [
            'name', 'rate_float', 'cost_clean', 'votes', 
            'location', 'location_clean', 'cuisines', 'cuisines_clean', 
            'address', 'online_order', 'book_table'
        ]
        df_cleaned = df[cols_to_keep]

        # Save to CSV
        df_cleaned.to_csv(CLEANED_DATA_PATH, index=False, encoding='utf-8')
        print(f"Cleaned dataset saved to: {CLEANED_DATA_PATH} (Shape: {df_cleaned.shape})")
        return df_cleaned

    except Exception as e:
        print(f"Ingestion failed: {e}")
        raise e

if __name__ == "__main__":
    run_ingestion()
