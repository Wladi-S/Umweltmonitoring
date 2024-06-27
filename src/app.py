import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import base64
import os
import plotly.express as px
from fetch import fetch_and_pivot_sensor_data, fetch_sensebox_info
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz
from neuralprophet import NeuralProphet
import shutil
import warnings
import threading
from initialize import update_data
from scheduler import start_scheduler
from utils import fetch_and_prepare_data, train_and_predict, train_and_update_forecast

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Get the directory of the current script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the path to the SVG icons directory relative to the current script location
SVG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "svg"))

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initialize the global forecast_df
forecast_df = pd.DataFrame()

# Initialize the global aggregated_df
aggregated_df = pd.DataFrame()


def get_last_valid_value(df, column):
    return df[column].dropna().iloc[-1]


def load_svg_icon(filename):
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    SVG_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "svg"))
    icon_path = os.path.join(SVG_DIR, filename)
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"No such file or directory: '{icon_path}'")
    return base64.b64encode(open(icon_path, "rb").read()).decode("ascii")


def calculate_sun_times(lat, lon):
    city = LocationInfo(
        name="Karlsruhe",
        region="Germany",
        timezone="Europe/Berlin",
        latitude=lat,
        longitude=lon,
    )
    timezone = pytz.timezone(city.timezone)
    s = sun(city.observer, date=datetime.now(), tzinfo=timezone)
    return s["sunrise"].strftime("%H:%M"), s["sunset"].strftime("%H:%M")


def create_sensor_card(title, value, icon_filename):
    encoded_image = load_svg_icon(icon_filename)
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
                                src=f"data:image/svg+xml;base64,{encoded_image}",
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
        style={
            "background-color": "#eff1f9",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_sensebox_info_card(info, sunrise_time, sunset_time):
    encoded_sunrise_icon = load_svg_icon("wi-sunrise.svg")
    encoded_sunset_icon = load_svg_icon("wi-sunset.svg")

    sunrise_card = dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Img(
                        src=f"data:image/svg+xml;base64,{encoded_sunrise_icon}",
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
            ),
            style={
                "background-color": "#eff1f9",
                "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
            },
        )
    )

    sunset_card = dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Img(
                        src=f"data:image/svg+xml;base64,{encoded_sunset_icon}",
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
            style={
                "background-color": "#eff1f9",
                "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
            },
        )
    )

    return dbc.Card(
        dbc.CardBody(
            [
                html.H2(info["name"], className="card-title"),
                create_info_row("Exposure", info["exposure"]),
                create_info_row(
                    "Aufgestellt am", info["created_at"].strftime("%d.%m.%Y")
                ),
                create_info_row(
                    "Letze Messung",
                    info["last_measurement_at"].strftime("%d.%m.%Y %H:%M"),
                ),
                create_info_row("Beschreibung", info["description"]),
                dbc.Row([sunrise_card, sunset_card], style={"marginTop": "20px"}),
            ],
        ),
        className="mb-3",
        style={
            "background-color": "#e7e9f5",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_info_row(title, value):
    return html.Div(
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
                        style={"display": "block", "fontSize": "20px"},
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
    )


def calculate_daily_stats(df):
    stats = []
    for i in range(1, 6):
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
    return stats[::-1]


def get_weather_icon(stats):
    if stats["sum_rain"] > 15:
        return "wi-day-rain.svg"
    elif stats["avg_radiation"] > 150:
        return "wi-day-sunny.svg"
    else:
        return "wi-day-cloudy.svg"


def create_daily_stats_card(stats):
    icon_filename = get_weather_icon(stats)
    encoded_image = load_svg_icon(icon_filename)

    return dbc.Card(
        dbc.CardBody(
            [
                html.H5(stats["day"], className="card-title"),
                html.P(stats["date"], className="card-date", style={"margin": "0"}),
                html.Img(
                    src=f"data:image/svg+xml;base64,{encoded_image}",
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
        style={
            "background-color": "#eff1f9",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_daily_stats_row(df):
    daily_stats = calculate_daily_stats(df)
    return dbc.Row([dbc.Col(create_daily_stats_card(stats)) for stats in daily_stats])


def create_main_content(df):
    return dbc.Card(
        dbc.CardBody(
            [
                create_daily_stats_row(df),
                create_sensor_cards_row(
                    df,
                    [
                        "Temperature in °C",
                        "Humidity in %",
                        "Windspeed in m/s",
                        "UV-B Radiation in W/m2",
                    ],
                ),
                create_sensor_cards_row(
                    df,
                    [
                        "Pressure in hPa",
                        "Rain (1h) in mm",
                        "Wind Direction in °",
                        "UV-A Radiation in W/m2",
                    ],
                ),
            ],
            style={"padding": "15px", "padding-bottom": "0px"},
        ),
        className="mb-3",
        style={
            "background-color": "#e7e9f5",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_sensor_cards_row(df, sensors):
    cards = []
    for sensor in sensors:
        value = f"{get_last_valid_value(df, sensor):.2f} {get_unit(sensor)}"
        cards.append(dbc.Col(create_sensor_card(sensor, value, get_icon(sensor))))
    return dbc.Row(cards)


def get_unit(sensor):
    units = {
        "Temperature in °C": "°C",
        "Humidity in %": "%",
        "Windspeed in m/s": "m/s",
        "UV-B Radiation in W/m2": "W/m²",
        "Pressure in hPa": "hPa",
        "Rain (1h) in mm": "mm",
        "Wind Direction in °": "°",
        "UV-A Radiation in W/m2": "W/m²",
    }
    return units.get(sensor, "")


def get_icon(sensor):
    icons = {
        "Temperature in °C": "wi-thermometer.svg",
        "Humidity in %": "wi-humidity.svg",
        "Windspeed in m/s": "wi-strong-wind.svg",
        "UV-B Radiation in W/m2": "wi-hot.svg",
        "Pressure in hPa": "wi-barometer.svg",
        "Rain (1h) in mm": "wi-umbrella.svg",
        "Wind Direction in °": "wi-direction.svg",
        "UV-A Radiation in W/m2": "wi-day-sunny.svg",
    }
    return icons.get(sensor, "wi-thermometer.svg")


# Fetch and prepare data
df = fetch_and_prepare_data()
sensebox_info = fetch_sensebox_info().iloc[0]
lon, lat = float(sensebox_info["longitude"]), float(sensebox_info["latitude"])
sunrise_time, sunset_time = calculate_sun_times(lat, lon)

# Initialize the forecast_df at the start
forecast_df = train_and_predict(df)


def create_forecast_card(time, value, icon_filename):
    encoded_image = load_svg_icon(icon_filename)
    return dbc.Card(
        dbc.CardBody(
            [
                html.Span(
                    time,
                    className="card-title",
                    style={
                        "display": "block",
                        "fontSize": "24px",
                        "marginBottom": "4px",
                    },
                ),
                html.Img(
                    src=f"data:image/svg+xml;base64,{encoded_image}",
                    className="card-icon",
                    style={"height": "60px", "width": "60px"},
                ),
                html.Span(
                    f"{value:.2f} °C",
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
        className="mb-3",
        style={
            "background-color": "#eff1f9",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_forecast_row(forecast_df):
    forecast_cards = []
    for i in range(1, len(forecast_df)):  # Start from index 1 to skip the first value
        if forecast_df.iloc[i]["y"] > forecast_df.iloc[i - 1]["y"]:
            icon_filename = "thermometer-warmer.svg"
        elif forecast_df.iloc[i]["y"] < forecast_df.iloc[i - 1]["y"]:
            icon_filename = "thermometer-colder.svg"
        else:
            icon_filename = "thermometer-celsius.svg"
        forecast_cards.append(
            dbc.Col(
                create_forecast_card(
                    forecast_df.iloc[i]["ds"].strftime("%H:%M"),
                    round(forecast_df.iloc[i]["y"], 1),
                    icon_filename,
                ),
                # width=1,  # Specify the width of each column
            )
        )
    return dbc.Row(forecast_cards)


# Create dropdown options for sensors
sensor_options = [
    {"label": label, "value": value}
    for label, value in [
        ("Temperatur", "Temperature in °C"),
        ("Luftfeuchtigkeit", "Humidity in %"),
        ("Windgeschwindigkeit", "Windspeed in m/s"),
        ("Luftdruck", "Pressure in hPa"),
        ("Regen", "Rain (1h) in mm"),
        ("UV-A Strahlung", "UV-A Radiation in W/m2"),
        ("UV-B Strahlung", "UV-B Radiation in W/m2"),
    ]
]

# Create dropdown options for aggregation methods
aggregation_options = [
    {"label": label, "value": value}
    for label, value in [
        ("Stündlich", "H"),
        ("Täglich", "D"),
        ("Wöchentlich", "W"),
    ]
]

try:
    encoded_map_icon = load_svg_icon("map.svg")
except FileNotFoundError as e:
    print(e)  # Print the error to see the problematic path

# Define the layout of the app
app.layout = html.Div(
    style={
        "padding": "5%",
        "display": "flex",
        "justifyContent": "center",
        "background-color": "#f5f5f5",
    },
    children=[
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000,  # in milliseconds
            n_intervals=0,
        ),
        html.Div(
            style={"maxWidth": "100%", "width": "100%"},
            children=[
                dbc.Row(
                    style={
                        "display": "flex",
                        "justifyContent": "flex-start",
                        "alignItems": "center",
                        "marginBottom": "20px",
                    },
                    children=[
                        dbc.Col(
                            html.H1(
                                "Umweltmonitoring für Karlsruhe",
                                style={
                                    "textAlign": "left",
                                    "fontSize": "60px",
                                    "color": "#50ae48",
                                },
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            html.Img(
                                id="open-modal",
                                src=f"data:image/svg+xml;base64,{encoded_map_icon}",
                                style={
                                    "height": "40px",
                                    "width": "40px",
                                    "cursor": "pointer",
                                },
                            ),
                            width="auto",
                        ),
                    ],
                ),
                dbc.Row(
                    style={"display": "flex", "justifyContent": "center"},
                    children=[
                        dbc.Col(
                            create_sensebox_info_card(
                                sensebox_info, sunrise_time, sunset_time
                            ),
                            id="sensebox-info-card",
                            width=3,
                        ),
                        dbc.Col(create_main_content(df), id="main-content", width=9),
                    ],
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H3(
                                "Heutige Vorhersage",
                                style={
                                    "textAlign": "left",
                                    "marginTop": "0px",
                                    "margin-bottom": "20px",
                                },
                            ),
                            html.Div(
                                id="forecast-row"
                            ),  # Change to Div to avoid nested rows
                            dbc.Row(dbc.Col(dcc.Graph(id="forecast-line-plot"))),
                        ],
                    ),
                    className="mb-3",
                    style={
                        "background-color": "#e7e9f5",
                        "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
                    },
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Row(
                                justify="center",
                                children=[
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="sensor-dropdown",
                                            options=sensor_options,
                                            placeholder="wähle Sensor",
                                            clearable=False,
                                            style={"width": "100%"},
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="aggregation-dropdown",
                                            options=aggregation_options,
                                            placeholder="wähle Aggregation",
                                            clearable=False,
                                            style={"width": "100%"},
                                        ),
                                        width=4,
                                    ),
                                ],
                                style={"width": "50%", "margin": "20px auto"},
                            ),
                            dbc.Row(dbc.Col(dcc.Graph(id="line-plot"))),
                        ]
                    ),
                    className="mb-3",
                    style={
                        "background-color": "#e7e9f5",
                        "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle("Karte"),
                            style={"background-color": "#e7e9f5"},
                        ),
                        dbc.ModalBody(
                            dcc.Graph(id="choropleth-map", style={"height": "70vh"}),
                            style={"background-color": "#e7e9f5", "padding": "0px"},
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close",
                                id="close-modal",
                                className="ml-auto",
                                style={"background-color": "#50ae48"},
                            ),
                            style={"background-color": "#e7e9f5"},
                        ),
                    ],
                    id="modal",
                    size="lg",
                ),
            ],
        ),
    ],
)


@app.callback(
    [Output("sensebox-info-card", "children"), Output("main-content", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_dashboard(n_intervals):
    # Fetch updated data
    df = fetch_and_prepare_data()
    sensebox_info = fetch_sensebox_info().iloc[0]
    lon, lat = float(sensebox_info["longitude"]), float(sensebox_info["latitude"])
    sunrise_time, sunset_time = calculate_sun_times(lat, lon)

    # Create updated components
    sensebox_info_card = create_sensebox_info_card(
        sensebox_info, sunrise_time, sunset_time
    )
    main_content = create_main_content(df)

    return sensebox_info_card, main_content


@app.callback(
    [Output("forecast-line-plot", "figure"), Output("forecast-row", "children")],
    [Input("interval-component", "n_intervals")],
)
def update_forecast_components(n_intervals):
    global forecast_df

    fig = px.line(
        forecast_df.iloc[1:],  # Skip the first value for the line plot
        x="ds",
        y="y",
        title="Temperatur Vorhersage (nächsten Stunden)",
        markers=True,
    ).update_layout(
        paper_bgcolor="#e7e9f5",
        plot_bgcolor="#e7e9f5",
        xaxis_title="Datum",
        yaxis_title="Temperatur",
    )

    fig.update_traces(line=dict(color="#50ae48"))

    forecast_row = create_forecast_row(forecast_df)

    return fig, forecast_row


@app.callback(
    Output("line-plot", "figure"),
    Input("sensor-dropdown", "value"),
    Input("aggregation-dropdown", "value"),
)
def update_line_plot(sensor, aggregation):
    if sensor is None or aggregation is None:
        return px.line(
            title="Wählen Sie den Sensor und die Aggregation aus, um Daten zu visualisieren."
        ).update_layout(
            paper_bgcolor="#e7e9f5",
            plot_bgcolor="#e7e9f5",
        )

    df_resampled = df.resample(aggregation, on="created_at")
    if sensor in ["Temperature in °C", "Humidity in %", "Pressure in hPa"]:
        df_agg = df_resampled.agg({sensor: ["min", "mean", "max"]})
        colors = {"min": "#70A1D7", "mean": "#A1DE93", "max": "#F47C7C"}
    elif sensor == "Rain (1h) in mm":
        df_agg = df_resampled.agg({sensor: "sum"})
        colors = {"sum": "#70A1D7"}
    else:
        df_agg = df_resampled.agg({sensor: ["mean", "max"]})
        colors = {"mean": "#A1DE93", "max": "#F47C7C"}

    df_agg.columns = ["_".join(col).strip() for col in df_agg.columns.values]
    df_agg.reset_index(inplace=True)

    fig = px.line(
        df_agg,
        x="created_at",
        y=df_agg.columns[1:],
        title=f"{sensor} über die Zeit ({aggregation})",
    ).update_layout(
        paper_bgcolor="#e7e9f5",
        plot_bgcolor="#e7e9f5",
        xaxis_title="Datum",
        yaxis_title=sensor,
    )

    # Update trace colors based on the aggregation type
    for trace in fig.data:
        trace_name = trace.name.split("_")[1]
        trace.line.color = colors.get(trace_name, "black")

    return fig


@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(Output("choropleth-map", "figure"), Input("open-modal", "n_clicks"))
def display_choropleth_map(n_clicks):
    if n_clicks is None:
        return {}

    df_sample = pd.DataFrame(
        {
            "lat": [lat, lat + 0.01, lat - 0.01],
            "lon": [lon, lon + 0.01, lon - 0.01],
            "value": [10, 20, 30],
        }
    )

    fig = px.choropleth_mapbox(
        df_sample,
        geojson=None,
        locations="value",
        color="value",
        mapbox_style="carto-positron",
        center={"lat": lat, "lon": lon},
        zoom=12,
        opacity=0.5,
    )
    fig.add_scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=14, color="red"),
        text=["Sensebox Location"],
        name="Sensebox",
    )
    fig.update_layout(paper_bgcolor="#e7e9f5")

    return fig


if __name__ == "__main__":

    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()

    update_data()  # Erstes Daten-Update beim Start
    train_and_update_forecast()  # Erstes Modelltraining beim Start

    app.run_server(debug=False)
