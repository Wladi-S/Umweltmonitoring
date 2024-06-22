import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

# Dash App initialisieren
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.Div(
            [
                html.H2("Sensor Data Dashboard"),
                html.P("Wählen Sie einen Sensor aus."),
                dcc.Dropdown(
                    id="sensor-dropdown",
                    options=[
                        {
                            "label": "Global Radiation",
                            "value": "Global Radiation in W/m2",
                        },
                        {"label": "Luftfeuchtigkeit", "value": "Humidity in %"},
                        {"label": "Luftdruck", "value": "Pressure in hPa"},
                        {"label": "Regen", "value": "Rain (1h) in mm"},
                        {"label": "Temperatur", "value": "Temperature in °C"},
                        {"label": "UV-A Radiation", "value": "UV-A Radiation in W/m2"},
                        {"label": "UV-B Radiation", "value": "UV-B Radiation in W/m2"},
                        # {'label': 'Wind Direction', 'value': 'Wind Direction in °'},
                        # {'label': 'Windspeed', 'value': 'Windspeed in m/s'}
                    ],
                    value="Temperature in °C",
                ),
            ],
            style={
                "width": "20%",
                "display": "inline-block",
                "vertical-align": "top",
                "padding": "20px",
            },
        ),
        html.Div(
            [dcc.Graph(id="sensor-graph")],
            style={"width": "75%", "display": "inline-block"},
        ),
    ]
)


@app.callback(Output("sensor-graph", "figure"), [Input("sensor-dropdown", "value")])
def update_graph(selected_sensor):
    filtered_df = df[["created_at", selected_sensor]].dropna()
    fig = px.line(
        filtered_df,
        x="created_at",
        y=selected_sensor,
        title=f"{selected_sensor} over Time",
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
