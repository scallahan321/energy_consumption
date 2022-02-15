from dash import *
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import pymysql
import os
from dotenv import load_dotenv #--only need this for local environment
import json

load_dotenv() #--only need this for local environment

#TESTING

db = os.environ.get('DB')
db_user = os.environ.get('DB_USERNAME')
db_password = os.environ.get("DB_PASSWORD")
#db_ssl = os.environ.get("DB_SSL")

#load state data csv for state names, abbreviations, and area in sq miles
state_data = pd.read_csv("state_data.csv")

#resource names and abbreviations
resource_abrevs = ['CL','NG','PA','SO','WY','BM','HY','NU']
resource_names = ['Coal','Natural Gas','Petroleum','Solar','Wind','Biomass','Hydroelectricity','Nuclear']

conn1 = pymysql.connect(
        host = db,
        user = db_user, 
        password = db_password,
        db = 'energy',
        ssl_ca = "global-bundle.pem"

        )
cur1 = conn1.cursor()

conn2 = pymysql.connect(
        host = db,
        user = db_user, 
        password = db_password,
        db = 'energy',
        )
cur2 = conn2.cursor()

colors = {
    'background': '#fcfdff',
    'text': '#edf7ff'
}

app = dash.Dash(__name__ , meta_tags=[{"name":"viewport","content":"width=device-width","initial-scale":"1"}])
server = app.server
        

app.layout = html.Div(children=[
    html.H1(style = {'text-align':'center'}, children = 'Energy Consumption'),

    html.Br(),
    html.Br(),

    html.Div(id = 'input_container', children = [

    html.Div(id = 'line_input', children = [
    
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
        value = ['CL']
    )
    ]),

    html.Div(id = 'map_input', children = [
        
    dcc.Dropdown(
        id = 'map_dropdown',
        className = 'drop',
        options = [{'label': i,'value':j} for i, j in zip(resource_names, resource_abrevs)],
        value = 'CL'
    ),

    html.Br(),

    dcc.Slider(id = 'year_slider', value = 1960, min = 1960, max = 2019, step = 1, marks = None, tooltip = { 'placement':'bottom'}),#, 'always_visible':True}),
    ]),

    ]),
    
    html.Br(),

    html.Div(id = 'chart_container', children = [
    
    html.Div(id = 'line_container', children = [
    
    dcc.Graph(
        id = 'line_chart',
    )
    ]),

    html.Div(id = 'map_container', children = [
     
    dcc.Graph(
        id = 'geo_chart'
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
    query = f'SELECT * FROM {selected_state}'
    cur1.execute(query)
    data = cur1.fetchall()
    j = json.dumps(data)
    l = json.loads(j)
    df = pd.DataFrame(l, columns = ['row','state_id','year','resource_id','population','consumption'])
    criterion = df['resource_id'].map(lambda x: x in selected_resources)
    fig = px.line(
        df.loc[criterion], 
        x = 'year', 
        y = 'consumption', 
        color = 'resource_id', 
        line_group = 'resource_id', 
        labels = {'year' : 'Year', 'consumption' : 'Consumption (BTU)'})

    fig.update_layout(
        legend_title = 'Resources'
    )
    num_selected = len(selected_resources)
    for i, name in enumerate(resource_names[0:num_selected]):       
        fig.data[i].name = name
    
    return fig

@app.callback(
    Output(component_id ='geo_chart', component_property = 'figure'),
    Input(component_id = 'map_dropdown', component_property = 'value'),
    Input(component_id = 'year_slider', component_property = 'value')
)

def update_map(resource, year):
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
        geo_scope = 'usa',
    )
    return fig

if __name__ == '__main__':
    
    app.run_server(debug=True)