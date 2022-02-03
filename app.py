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

#load state data csv for state names, abbreviations, and area in sq miles
state_data = pd.read_csv("state_data.csv")

#resource names and abbreviations
resource_abrevs = ['CL','NG','PA','SO','WY','BM','HY','NU']
resource_names = ['Coal','Natural Gas','Petroleum','Solar','Wind','Biomass','Hydroelectricity','Nuclear']

# To connect MySQL database
engine = sqlalchemy.create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db}/energy")
conn = engine.connect()

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),
    dcc.Dropdown(
        id = 'state_dropdown',
        options=[
        {'label': i, 'value': i} for i in state_data['state']] ,
        value='Alabama'
    ),

    dcc.Checklist(
        id = 'resource_checklist',
        options=[ {'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value=['CL']
    ),

    dcc.Graph(
        id='graph-1'
    )
])
@app.callback(
    Output(component_id='graph-1',component_property='figure'),
    Input(component_id='state_dropdown',component_property='value'),
    Input(component_id ='resource_checklist',component_property='value')
)

def update_state(selected_state,selected_resources): 
    #checked = selected_resources
    query = sqlalchemy.text(f'SELECT * FROM {selected_state}')
    df = pd.read_sql(query,conn)
    criterion = df['resource_id'].map(lambda x: x in selected_resources)
    fig = px.line(df.loc[criterion], x="year", y="consumption", color="resource_id",line_group="resource_id")
    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True)