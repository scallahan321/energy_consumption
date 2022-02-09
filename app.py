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
import json


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
#engine = sqlalchemy.create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db}/energy")
#conn = engine.connect()

conn1 = pymysql.connect(
        host = db,
        user = db_user, 
        password = db_password,
        db = 'energy',
        )
cur1 = conn1.cursor()

conn2 = pymysql.connect(
        host = db,
        user = db_user, 
        password = db_password,
        db = 'energy',
        )
cur2 = conn2.cursor()

app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(style = {'text-align':'center'}, children = 'Energy Consumption'),

    html.Br(),
   
    html.Div(id = 'chart_container', style = {'display':'flex', 'width':'100%'}, children = [

    html.Div(id = 'line_chart_container', style = {'flex':'2'}, children = [
    
    dcc.Dropdown(
        id = 'state_dropdown',
        className = 'drop',
        options = [{'label': i, 'value': i} for i in state_data['state']] ,
        value = 'Alabama'
    ),
    html.Br(),

    dcc.Checklist(
        id = 'resource_checklist',
        options = [{'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value = ['CL'],
        style = {'display':'flex', 'justify-content':'center'}
    ),
    dcc.Graph(
        id = 'line_chart'
    )
    ]),
    html.Div(id = 'map_chart_container', style = {'flex':'2'}, children = [
        
    dcc.Dropdown(
        id = 'map_dropdown',
        className = 'drop',
        options = [{'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value = 'CL'
    ),

    html.Br(),

    dcc.Slider(id = 'year_slider', value = 1960, min = 1960, max = 2019, step = 1, tooltip = { 'placement':'bottom', 'always_visible':True}),

    dcc.Graph(
        id= 'geo_chart'
    )
    ])
    ])

])

@app.callback(
    Output(component_id = 'line_chart', component_property = 'figure'),
    Input(component_id = 'state_dropdown', component_property = 'value'),
    Input(component_id = 'resource_checklist', component_property = 'value')
)

def update_state(selected_state,selected_resources): 
    #a view from the db will be queried every time the dropdown selection changes
    #query = sqlalchemy.text(f'SELECT * FROM {selected_state}')
    #read query into pandas dataframe
    #df = pd.read_sql(query, conn)
    #boolean condition for indexing df based on the resources checked by user
    query = f'SELECT * FROM {selected_state}'
    cur1.execute(query)
    data = cur1.fetchall()
    j = json.dumps(data)
    l = json.loads(j)
    df = pd.DataFrame(l,columns = ['row','state_id','year','resource_id','population','consumption'])
    criterion = df['resource_id'].map(lambda x: x in selected_resources)
    fig = px.line(df.loc[criterion], x = "year", y = "consumption", color = "resource_id",line_group = "resource_id")
    return fig

@app.callback(
    Output(component_id ='geo_chart', component_property = 'figure'),
    Input(component_id = 'map_dropdown', component_property = 'value'),
    Input(component_id = 'year_slider', component_property = 'value')
)

def update_map(resource, year):
    #query to grab all the data from facts table for corresponding resource
    #query = sqlalchemy.text(f'SELECT * FROM facts WHERE resource_id = "{selected_resource}"')
    #read query into pandas dataframe
    #df = pd.read_sql(query, conn)
    query = f'SELECT * FROM facts WHERE resource_id = "{resource}"'
    cur2.execute(query)
    data = cur2.fetchall()
    j = json.dumps(data)
    l = json.loads(j)
    df = pd.DataFrame(l, columns = ['row','state_id','year','resource_id','population','consumption'])
    df['per_capita'] = df['consumption'] / df['population']
    current_df = df[df['year'] == year]

    fig = go.Figure(data = go.Choropleth(
        locations = state_data['abrev'],
        z = current_df['per_capita'],
        locationmode = 'USA-states',
        colorscale = 'blues',
        colorbar_title = "Per Capita Consumption (BTU)",
        text = state_data['state']
    ))
    fig.update_layout(
        geo_scope = 'usa'
    )
    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True)