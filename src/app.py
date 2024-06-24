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

# Set the path to the SVG icons directory relative to the app.py location
SVG_DIR = os.path.join("..", "svg")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def fetch_and_prepare_data():
    df_pivot = fetch_and_pivot_sensor_data()
    return df_pivot


df = fetch_and_prepare_data()
sensebox_info = fetch_sensebox_info().iloc[0]  # Assuming there's only one sensebox

lon = float(sensebox_info["longitude"])
lat = float(sensebox_info["latitude"])

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
        style={
            "background-color": "#eff1f9",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
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
                style={
                    "textAlign": "center",
                },
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
            style={
                "background-color": "#eff1f9",
                "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
            },
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
                                    info["created_at"].strftime("%d.%m.%Y"),
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
                                        "%d.%m.%d %H:%M"
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
        style={
            "background-color": "#e7e9f5",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def calculate_daily_stats(df):
    stats = []
    for i in range(5):
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
        style={
            "background-color": "#eff1f9",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


def create_daily_stats_row(df):
    daily_stats = calculate_daily_stats(df)
    return dbc.Row(
        children=[dbc.Col(create_daily_stats_card(stats)) for stats in daily_stats],
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
                                "Windgeschwindigkeit",
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
                                "wi-umbrella.svg",
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
        style={
            "background-color": "#e7e9f5",
            "box-shadow": "rgba(0, 0, 0, 0.1) 0px 5px 15px 0px",
        },
    )


# Create dropdown options for sensors
sensor_options = [
    {"label": "Temperatur", "value": "Temperature in °C"},
    {"label": "Luftfeuchtigkeit", "value": "Humidity in %"},
    {"label": "Windgeschwindigkeit", "value": "Windspeed in m/s"},
    {"label": "Luftdruck", "value": "Pressure in hPa"},
    {"label": "Regen", "value": "Rain (1h) in mm"},
    {"label": "UV-A Strahlung", "value": "UV-A Radiation in W/m2"},
    {"label": "UV-B Strahlung", "value": "UV-B Radiation in W/m2"},
]

# Create dropdown options for aggregation methods
aggregation_options = [
    {"label": "Stündlich", "value": "H"},
    {"label": "Täglich", "value": "D"},
    {"label": "Wöchentlich", "value": "W"},
]

# Encode the map.svg file
map_icon_path = os.path.join(SVG_DIR, "map.svg")
encoded_map_icon = base64.b64encode(open(map_icon_path, "rb").read()).decode("ascii")

app.layout = html.Div(
    style={
        "padding": "5%",
        "display": "flex",
        "justifyContent": "center",
        "background-color": "#f5f5f5",
    },
    children=[
        html.Div(
            style={
                "maxWidth": "100%",
                "width": "100%",
            },
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
                                src="data:image/svg+xml;base64,{}".format(
                                    encoded_map_icon
                                ),
                                style={
                                    "height": "40px",
                                    "width": "40px",
                                    "cursor": "pointer",
                                },
                            ),
                            width="auto",  # Automatic width adjustment
                        ),
                    ],
                ),
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
                                style={
                                    "width": "50%",
                                    "margin": "20px auto",
                                },
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
                            style={
                                "background-color": "#e7e9f5",
                            },
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
        )

    if aggregation == "H":
        df_resampled = df.resample("h", on="created_at")
    elif aggregation == "D":
        df_resampled = df.resample("D", on="created_at")
    else:
        df_resampled = df.resample("W", on="created_at")

    if sensor in ["Temperature in °C", "Humidity in %", "Pressure in hPa"]:
        df_agg = df_resampled.agg({sensor: ["min", "mean", "max"]})
    elif sensor == "Rain (1h) in mm":
        df_agg = df_resampled.agg({sensor: "sum"})
    else:
        df_agg = df_resampled.agg({sensor: ["mean", "max"]})

    # Flatten column names
    df_agg.columns = ["_".join(col).strip() for col in df_agg.columns.values]
    df_agg.reset_index(inplace=True)

    fig = px.line(
        df_agg,
        x="created_at",
        y=df_agg.columns[1:],
        title=f"{sensor} über die Zeit ({aggregation})",
    ).update_layout(
        paper_bgcolor="#e7e9f5",
    )

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

    # Create a sample choropleth map using plotly express
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

    # Add a marker for the Sensebox location
    fig.add_scattermapbox(
        lat=[lat],
        lon=[lon],
        mode="markers",
        marker=dict(size=14, color="red"),
        text=["Sensebox Location"],
        name="Sensebox",
    )

    fig.update_layout(
        paper_bgcolor="#e7e9f5",
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
