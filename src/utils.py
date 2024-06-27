import pandas as pd
from fetch import fetch_and_pivot_sensor_data
from neuralprophet import NeuralProphet
import shutil
from datetime import datetime


def fetch_and_prepare_data():
    df_pivot = fetch_and_pivot_sensor_data()
    return df_pivot


def train_and_predict(df):
    now = datetime.now()
    hourly_forecast = df[["created_at", "Temperature in °C"]].dropna()
    hourly_forecast.set_index("created_at", inplace=True)
    hourly_forecast["Temperature in °C"] = hourly_forecast["Temperature in °C"].astype(
        float
    )
    hourly_forecast = hourly_forecast.resample("1H").max().dropna()
    hourly_forecast.reset_index(inplace=True)
    hourly_forecast.columns = ["ds", "y"]
    now = datetime.now()
    if now.minute != 0:
        hourly_forecast = hourly_forecast[
            :-1
        ]  # Remove the last hour only if we are not at the full hour
    m = NeuralProphet()
    model = m.fit(hourly_forecast, freq="H", epochs=100)
    future = m.make_future_dataframe(hourly_forecast, periods=6)
    forecast = m.predict(future)
    forecast = forecast[["ds", "yhat1"]]
    forecast.columns = ["ds", "y"]
    shutil.rmtree("lightning_logs", ignore_errors=True)
    return pd.concat([hourly_forecast[-3:], forecast])


def train_and_update_forecast():
    global forecast_df
    df = fetch_and_prepare_data()
    forecast_df = train_and_predict(df)
    print("Forecast updated.")
