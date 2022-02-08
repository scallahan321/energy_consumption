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
        options = [
        {'label': i, 'value': i} for i in state_data['state']] ,
        value = 'Alabama'
    ),

    dcc.Checklist(
        id = 'resource_checklist',
        options = [{'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value = ['CL']
    ),

    dcc.Graph(
        id = 'line_chart'
    ),

    dcc.Dropdown(
        id = 'map_dropdown',
        options = [{'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value = ['CL']
    ),

    dcc.Slider(id='year_slider', value=1960, min=1960, max=2019, step=1),
    
    dcc.Graph(
        id= 'geo_chart'
    )

])

@app.callback(
    Output(component_id='line_chart', component_property='figure'),
    Input(component_id='state_dropdown', component_property='value'),
    Input(component_id ='resource_checklist', component_property='value')
)

def update_state(selected_state,selected_resources): 
    #a view from the db will be queried every time the dropdown selection changes
    query = sqlalchemy.text(f'SELECT * FROM {selected_state}')
    #read query into pandas dataframe
    df = pd.read_sql(query,conn)
    #boolean condition for indexing df based on the resources checked by user
    criterion = df['resource_id'].map(lambda x: x in selected_resources)
    fig = px.line(df.loc[criterion], x="year", y="consumption", color="resource_id",line_group="resource_id")
    return fig

@app.callback(
    Output(component_id ='geo_chart', component_property = 'figure'),
    Input(component_id = 'year_slider',)
)

def update_map():
    print('hi')

if __name__ == '__main__':
    
    app.run_server(debug=True)