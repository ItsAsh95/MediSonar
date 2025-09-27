# disease_outbreak_app/main_router.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb

# --- Setup ---
router = APIRouter(
    prefix="/disease-outbreak",
    tags=["Disease Outbreak Predictor Application"]
)

# Define paths relative to this file's location
APP_BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_BASE_DIR / "static"
DATA_PATH = APP_BASE_DIR / "data" / "processed" / "measles_cases_processed_timeseries.csv"

# --- Caching Mechanism (same as your original app.py) ---
# This will hold the forecast data after it's generated once.
FORECAST_DATA_CACHE = None

def generate_and_cache_forecast():
    """
    Loads data, trains model, and generates forecast.
    This function is called once on server startup.
    """
    global FORECAST_DATA_CACHE
    try:
        print("DISEASE_OUTBREAK_APP: Loading and processing data for forecast...")
        # --- 1. Load and Prepare Data ---
        df_cases = pd.read_csv(DATA_PATH, index_col='Year', parse_dates=True)
        df_long = df_cases.melt(ignore_index=False, var_name='CountryCode', value_name='Cases').reset_index()
        df_long.sort_values(by=['CountryCode', 'Year'], inplace=True)
        df_long['Cases_Next_Year'] = df_long.groupby('CountryCode')['Cases'].shift(-1)
        df_long['Cases_Lag_1'] = df_long.groupby('CountryCode')['Cases'].shift(1)
        df_long['Year_Num'] = df_long['Year'].dt.year
        df_final = df_long.dropna(subset=['Cases_Next_Year', 'Cases_Lag_1'])

        # --- 2. Train Model on All Data ---
        features = ['Cases', 'Cases_Lag_1', 'Year_Num']
        target = 'Cases_Next_Year'
        X_full = df_final[features]
        y_full = df_final[target]
        model_full = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=500, learning_rate=0.05)
        model_full.fit(X_full, y_full, verbose=False)
        print("DISEASE_OUTBREAK_APP: Model training complete.")

        # --- 3. Prepare Data for Prediction ---
        most_recent_year_data = df_long[df_long['Year'] == df_long['Year'].max()].copy()
        if 'Cases_Lag_1' in most_recent_year_data.columns:
            most_recent_year_data.drop(columns=['Cases_Lag_1'], inplace=True)
        prev_year = df_long['Year'].max() - pd.DateOffset(years=1)
        prev_year_cases = df_long[df_long['Year'] == prev_year][['CountryCode', 'Cases']]
        most_recent_year_data = pd.merge(most_recent_year_data, prev_year_cases.rename(columns={'Cases': 'Cases_Lag_1'}), on='CountryCode', how='left')
        X_predict = most_recent_year_data[features].dropna()

        # --- 4. Generate & Score Forecast ---
        future_forecasts = model_full.predict(X_predict)
        forecast_df = X_predict.copy()
        forecast_df['Forecasted_Cases'] = np.maximum(0, future_forecasts)
        forecast_df = pd.merge(forecast_df, most_recent_year_data[['CountryCode']], left_index=True, right_index=True, how='left')

        end_year = df_cases.index.max().year
        start_year = end_year - 10
        historical_stats = df_cases.loc[str(start_year):str(end_year)].agg(['mean', 'std']).transpose()
        historical_stats.rename(columns={'mean': 'Mean_Cases_10Y', 'std': 'Std_Cases_10Y'}, inplace=True)
        historical_stats.fillna(0, inplace=True)
        results_df = pd.merge(forecast_df, historical_stats, left_on='CountryCode', right_index=True)

        def assign_risk_level(row):
            mean, std, forecast = row['Mean_Cases_10Y'], row['Std_Cases_10Y'], row['Forecasted_Cases']
            if std == 0: return 'High' if forecast > mean else 'Low'
            if forecast > mean + (2 * std): return 'High'
            elif forecast > mean + std: return 'Medium'
            else: return 'Low'
        
        results_df['Risk_Level'] = results_df.apply(assign_risk_level, axis=1)

        # Convert DataFrame to a list of dictionaries for caching
        FORECAST_DATA_CACHE = results_df.to_dict(orient='records')
        print("DISEASE_OUTBREAK_APP: Forecast generated and cached successfully.")

    except Exception as e:
        print(f"CRITICAL ERROR in Disease Outbreak App during startup: {e}")
        FORECAST_DATA_CACHE = {"error": str(e)}

# --- API Endpoint ---
@router.get("/api/global-forecast")
async def get_global_forecast():
    if FORECAST_DATA_CACHE is None:
        raise HTTPException(status_code=503, detail="Forecast data is not ready or failed to generate.")
    if "error" in FORECAST_DATA_CACHE:
        raise HTTPException(status_code=500, detail=f"Error during forecast generation: {FORECAST_DATA_CACHE['error']}")
    return FORECAST_DATA_CACHE

# --- Serve this sub-app's HTML frontend ---
@router.get("/", response_class=FileResponse, include_in_schema=False)
async def serve_outbreak_predictor_ui():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Outbreak Predictor UI (index.html) not found.")
    return FileResponse(index_path)