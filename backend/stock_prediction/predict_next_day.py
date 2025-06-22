import time
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
import pytz
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from pandas.tseries.offsets import BDay

LOOK_BACK = 20  # Must match your training setup

def fetch_latest_data(stock_symbol, look_back=LOOK_BACK, retries=3, initial_delay=2):
    delay = initial_delay
    for attempt in range(1, retries + 1):
        try:
            # Download extra days to ensure enough business days
            data = yf.download(stock_symbol, period=f"{look_back+5}d")
            data = data.asfreq('B').ffill().bfill()
            if len(data) < look_back:
                raise ValueError("Not enough data available for ticker.")
            window = data['Close'].tail(look_back).values.reshape(1, look_back)
            last_date = data.index[-1]
            return window, last_date
        except Exception as e:
            # Check if the error message indicates rate limiting
            if "Rate limited" in str(e):
                print(f"Rate limit encountered for {stock_symbol} on attempt {attempt}. Waiting {delay} seconds before retrying.")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise e
    raise Exception(f"Max retries reached for {stock_symbol}.")

def predict_next_day_price_new(stock_symbol, actual_next_day_price=None):
    
    import os
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODEL_DIR = os.path.join(BASE_DIR, "models")
    
    prefix = stock_symbol.split('.')[0]
    deep_model_path = os.path.join(MODEL_DIR, f"{prefix}_deep_model.h5")
    xgb_model_path = os.path.join(MODEL_DIR, f"{prefix}_xgb_model.pkl")
    input_scaler_path = os.path.join(MODEL_DIR, f"{prefix}_input_scaler.pkl")
    target_scaler_path = os.path.join(MODEL_DIR, f"{prefix}_target_scaler.pkl")
    
    try:
        deep_model = load_model(deep_model_path)
        xgb_model = joblib.load(xgb_model_path)
        input_scaler = joblib.load(input_scaler_path)
        target_scaler = joblib.load(target_scaler_path)
    except Exception as e:
        return {"error": f"Error loading models for {stock_symbol}: {e}"}
    
    try:
        latest_window, last_date = fetch_latest_data(stock_symbol, look_back=LOOK_BACK)
    except Exception as e:
        return {"error": f"Error fetching historical data for {stock_symbol}: {e}"}
    
    # Fetch the current price using yf.Ticker.info (this is the "real-time" price, though it might be delayed)
    try:
        ticker_obj = yf.Ticker(stock_symbol)
        current_price = ticker_obj.info.get('regularMarketPrice')
        if current_price is None:
            # Fallback to last available closing price if current price is not available.
            current_price = latest_window[0, -1]
    except Exception as e:
        current_price = latest_window[0, -1]
    
    # Convert last_date (from historical data) to Indian Standard Time (IST)
    indian_tz = pytz.timezone('Asia/Kolkata')
    last_date_ist = pd.to_datetime(last_date).tz_localize('UTC').tz_convert(indian_tz)
    next_business_day_ist = last_date_ist + BDay(1)
    
    # Preprocess the historical window for the model input.
    latest_scaled = input_scaler.transform(latest_window)
    latest_model_input = latest_scaled.reshape(1, LOOK_BACK, 1)
    
    try:
        deep_pred = deep_model.predict(latest_model_input, verbose=0).flatten()
        xgb_pred = xgb_model.predict(latest_model_input.reshape(1, -1))
    except Exception as e:
        return {"error": f"Error during prediction for {stock_symbol}: {e}"}
    
    # Ensemble prediction: 70% XGBoost, 30% Deep model.
    ensemble_pred = 0.70 * xgb_pred + 0.30 * deep_pred
    next_day_diff = target_scaler.inverse_transform(ensemble_pred.reshape(-1, 1))[0, 0]
    
    # Instead of using the last close from historical data, use the current price.
    predicted_price = current_price + next_day_diff
    
    result = {
        "ticker": stock_symbol.upper(),
        "last_date": last_date_ist.strftime('%Y-%m-%d'),
        "next_business_day": next_business_day_ist.strftime('%Y-%m-%d'),
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2)
    }
    
    if actual_next_day_price is not None:
        try:
            actual_next_day_price = float(actual_next_day_price)
            mae = abs(actual_next_day_price - predicted_price)
            mape = abs(actual_next_day_price - predicted_price) / actual_next_day_price * 100
            result["actual_price"] = actual_next_day_price
            result["MAE"] = round(mae, 4)
            result["MAPE"] = round(mape, 2)
        except Exception as e:
            result["error"] = f"Error computing error metrics: {e}"
    
    return result

if __name__ == '__main__':
    ticker = input("Enter stock ticker (e.g. RELIANCE.NS): ")
    result = predict_next_day_price_new(ticker)
    print(result)
