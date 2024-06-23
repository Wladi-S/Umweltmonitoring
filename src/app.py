import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import os
from fetch import (
    fetch_and_pivot_sensor_data,
    fetch_sensebox_info,
)
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz  # To handle timezones

# Set the path to the SVG icons directory relative to the app.py location
SVG_DIR = os.path.join("..", "svg")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def fetch_and_prepare_data():
    df_pivot = fetch_and_pivot_sensor_data()
    return df_pivot


df = fetch_and_prepare_data()
sensebox_info = fetch_sensebox_info().iloc[0]  # Assuming there's only one sensebox

lon = sensebox_info["longitude"]
lat = sensebox_info["latitude"]

# Calculate sunrise and sunset times with timezone adjustment
city = LocationInfo(
    name="Karlsruhe",
    region="Germany",
    timezone="Europe/Berlin",
    latitude=lat,
    longitude=lon,
)
timezone = pytz.timezone(city.timezone)  # Get the timezone of the location
s = sun(city.observer, date=datetime.now(), tzinfo=timezone)
sunrise_time = s["sunrise"].strftime("%H:%M")
sunset_time = s["sunset"].strftime("%H:%M")


def get_last_valid_value(df, column):
    return df[column].dropna().iloc[-1]


def create_sensor_card(title, value, icon_filename):
    icon_path = os.path.join(SVG_DIR, icon_filename)
    encoded_image = base64.b64encode(open(icon_path, "rb").read()).decode("ascii")
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    title,
                                    className="card-title",
                                    style={
                                        "display": "block",
                                        "fontSize": "14px",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.Span(
                                    value,
                                    className="card-value",
                                    style={
                                        "display": "block",
                                        "fontSize": "24px",
                                        "fontWeight": "bold",
                                    },
                                ),
                            ],
                            style={"flex": "1", "textAlign": "left"},
                        ),
                        html.Div(
                            html.Img(
                                src="data:image/svg+xml;base64,{}".format(
                                    encoded_image
                                ),
                                className="card-icon",
                                style={"height": "60px", "width": "60px"},
                            ),
                            style={"textAlign": "right"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                    },
                ),
            ],
        ),
        className="mb-3",
    )


def create_sensebox_info_card(info):
    sunrise_icon = os.path.join(SVG_DIR, "wi-sunrise.svg")
    sunset_icon = os.path.join(SVG_DIR, "wi-sunset.svg")

    encoded_sunrise_icon = base64.b64encode(open(sunrise_icon, "rb").read()).decode(
        "ascii"
    )
    encoded_sunset_icon = base64.b64encode(open(sunset_icon, "rb").read()).decode(
        "ascii"
    )

    sunrise_card = dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Img(
                        src="data:image/svg+xml;base64,{}".format(encoded_sunrise_icon),
                        style={"height": "60px", "width": "60px"},
                    ),
                    html.Span(
                        sunrise_time,
                        className="card-value",
                        style={
                            "display": "block",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                        },
                    ),
                ],
                style={"textAlign": "center"},
            )
        )
    )

    sunset_card = dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Img(
                        src="data:image/svg+xml;base64,{}".format(encoded_sunset_icon),
                        style={"height": "60px", "width": "60px"},
                    ),
                    html.Span(
                        sunset_time,
                        className="card-value",
                        style={
                            "display": "block",
                            "fontSize": "24px",
                            "fontWeight": "bold",
                        },
                    ),
                ],
                style={"textAlign": "center"},
            ),
        )
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H2(
                    info["name"], className="card-title", style={"color": "#50ae48"}
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Exposure",
                                    className="card-title",
                                    style={
                                        "display": "block",
                                        "fontSize": "14px",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.Span(
                                    info["exposure"],
                                    className="card-value",
                                    style={
                                        "display": "block",
                                        "fontSize": "20px",
                                    },
                                ),
                            ],
                            style={"flex": "1", "textAlign": "left"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Aufgestellt am",
                                    className="card-title",
                                    style={
                                        "display": "block",
                                        "fontSize": "14px",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.Span(
                                    info["created_at"].strftime("%Y-%m-%d"),
                                    className="card-value",
                                    style={
                                        "display": "block",
                                        "fontSize": "20px",
                                    },
                                ),
                            ],
                            style={"flex": "1", "textAlign": "left"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Letze Messung",
                                    className="card-title",
                                    style={
                                        "display": "block",
                                        "fontSize": "14px",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.Span(
                                    info["last_measurement_at"].strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    className="card-value",
                                    style={
                                        "display": "block",
                                        "fontSize": "20px",
                                    },
                                ),
                            ],
                            style={"flex": "1", "textAlign": "left"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Beschreibung",
                                    className="card-title",
                                    style={
                                        "display": "block",
                                        "fontSize": "14px",
                                        "marginBottom": "4px",
                                    },
                                ),
                                html.Span(
                                    info["description"],
                                    className="card-value",
                                    style={
                                        "display": "block",
                                        "fontSize": "20px",
                                    },
                                ),
                            ],
                            style={"flex": "1", "textAlign": "left"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                    },
                ),
                dbc.Row([sunrise_card, sunset_card], style={"marginTop": "20px"}),
            ],
        ),
        className="mb-3",
    )


def calculate_daily_stats(df):
    stats = []
    for i in range(8):
        day = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_data = df[df["created_at"].dt.strftime("%Y-%m-%d") == day_str]
        if not day_data.empty:
            max_temp = day_data["Temperature in °C"].max()
            min_temp = day_data["Temperature in °C"].min()
            sum_rain = day_data["Rain (1h) in mm"].sum()
            avg_radiation = day_data["Global Radiation in W/m2"].mean()
            stats.append(
                {
                    "day": day.strftime("%A")[:3],
                    "date": day.strftime("%d.%m"),
                    "max_temp": max_temp,
                    "min_temp": min_temp,
                    "sum_rain": sum_rain,
                    "avg_radiation": avg_radiation,
                }
            )
    return stats[::-1]  # Reverse to have the oldest day on the left


def get_weather_icon(stats):
    if stats["sum_rain"] > 15:
        icon_filename = "wi-day-rain.svg"
    elif stats["avg_radiation"] > 150:  # Threshold for sunny
        icon_filename = "wi-day-sunny.svg"
    else:
        icon_filename = "wi-day-cloudy.svg"
    return icon_filename


def create_daily_stats_card(stats):
    icon_filename = get_weather_icon(stats)
    icon_path = os.path.join(SVG_DIR, icon_filename)
    encoded_image = base64.b64encode(open(icon_path, "rb").read()).decode("ascii")

    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(stats["day"], className="card-title"),
                html.P(stats["date"], className="card-date", style={"margin": "0"}),
                html.Img(
                    src="data:image/svg+xml;base64,{}".format(encoded_image),
                    style={"height": "60px", "width": "60px", "margin": "9px"},
                ),
                html.P(
                    f"{stats['max_temp']:.2f} °C",
                    style={"fontSize": "24px", "fontWeight": "bold", "margin": "0"},
                ),
                html.P(f"{stats['min_temp']:.2f} °C", style={"margin": "0"}),
                html.P(f"{stats['sum_rain']:.2f} mm", style={"margin": "0"}),
            ],
            style={"textAlign": "center"},
        ),
        className="mb-3",
    )


def create_daily_stats_row(df):
    daily_stats = calculate_daily_stats(df)
    return dbc.Row(
        children=[dbc.Col(create_daily_stats_card(stats)) for stats in daily_stats]
    )


def create_main_content(df):
    return dbc.Card(
        dbc.CardBody(
            [
                create_daily_stats_row(df),
                dbc.Row(
                    children=[
                        dbc.Col(
                            create_sensor_card(
                                "Temperatur",
                                f"{get_last_valid_value(df, 'Temperature in °C'):.2f} °C",
                                "wi-thermometer.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "Luftfeuchtigkeit",
                                f"{get_last_valid_value(df, 'Humidity in %'):.2f} %",
                                "wi-humidity.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "Wind Geschwindigkeit",
                                f"{get_last_valid_value(df, 'Windspeed in m/s'):.2f} m/s",
                                "wi-strong-wind.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "UV-B Strahlung",
                                f"{get_last_valid_value(df, 'UV-B Radiation in W/m2'):.2f} W/m²",
                                "wi-hot.svg",
                            ),
                        ),
                    ]
                ),
                dbc.Row(
                    children=[
                        dbc.Col(
                            create_sensor_card(
                                "Luftdruck",
                                f"{get_last_valid_value(df, 'Pressure in hPa'):.2f} hPa",
                                "wi-barometer.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "Regen (1h)",
                                f"{get_last_valid_value(df, 'Rain (1h) in mm'):.2f} mm",
                                "wi-raindrop.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "Wind Richtung",
                                f"{get_last_valid_value(df, 'Wind Direction in °'):.2f} °",
                                "wi-direction.svg",
                            ),
                        ),
                        dbc.Col(
                            create_sensor_card(
                                "UV-A Strahlung",
                                f"{get_last_valid_value(df, 'UV-A Radiation in W/m2'):.2f} W/m²",
                                "wi-day-sunny.svg",
                            ),
                        ),
                    ],
                ),
            ],
            style={
                "padding": "15px",
                "padding-bottom": "0px",
            },
        ),
        className="mb-3",
    )


app.layout = html.Div(
    style={
        "padding": "5%",
        "display": "flex",
        "justifyContent": "center",
    },
    children=[
        html.Div(
            style={
                "maxWidth": "100%",
                "width": "100%",
            },
            children=[
                dbc.Row(
                    style={"display": "flex", "justifyContent": "center"},
                    children=[
                        dbc.Col(
                            create_sensebox_info_card(sensebox_info),
                            width=3,  # 1/4 of the row
                        ),
                        dbc.Col(
                            create_main_content(df),
                            width=9,  # 3/4 of the row
                        ),
                    ],
                ),
            ],
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
