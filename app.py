from dash import *
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import pymysql
import sqlalchemy
import os
from dotenv import load_dotenv

load_dotenv()

db = os.environ.get('DB')
db_user = os.environ.get('DB_USERNAME')
db_password = os.environ.get("DB_PASSWORD")

# To connect MySQL database
engine = sqlalchemy.create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db}/energy")
conn = engine.connect()

query = sqlalchemy.text("SELECT * FROM facts LIMIT 20")
df = pd.read_sql(query,conn)

app = dash.Dash(__name__)

fig = px.bar(df, x="year", y="consumption", color="resource_id", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    
    app.run_server(debug=True)