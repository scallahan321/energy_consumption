import pandas as pd
import requests
import mysql.connector
import csv
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get('EIA_KEY')
db = os.environ.get('DB_ENDPOINT')
db_user = os.environ.get('DB_USERNAME')
db_password = os.environ.get("DB_PASSWORD")

mydb = mysql.connector.connect(
  host=db,
  user=db_user,
  password=db_password
)

cur = mydb.cursor()
cur.execute("USE energy")

#create facts table 
create_fact_table = "CREATE TABLE IF NOT EXISTS facts(row_id INT NOT NULL AUTO_INCREMENT,state_id VARCHAR(2),year YEAR(4),resource_id VARCHAR(2),population DOUBLE (9,2),consumption DOUBLE(9,2),PRIMARY KEY(row_id))"
cur.execute(create_fact_table)

#create state_dim table
create_state_table = "CREATE TABLE IF NOT EXISTS state_dim (state_id VARCHAR(2), state_name VARCHAR(15), area DOUBLE(9,2), PRIMARY KEY (state_id))"
cur.execute(create_state_table)

#create resource_dim table
create_resource_table = "CREATE TABLE IF NOT EXISTS resource_dim (resource_id VARCHAR(2), resource_name VARCHAR(15), unit_measurement VARCHAR (10), PRIMARY KEY (resource_id))"
cur.execute(create_resource_table)

#alter tables to add foreign key constraints

add_fk_state = "ALTER TABLE facts ADD FOREIGN KEY(state_id) REFERENCES state_dim(state_id)"
cur.execute(add_fk_state)

add_fk_resource = "ALTER TABLE facts ADD FOREIGN KEY (resource_id) REFERENCES resource_dim(resource_id)"
cur.execute(add_fk_resource)

#### get state names, abbreviations, and area
page = pd.read_html("https://en.wikipedia.org/wiki/List_of_states_and_territories_of_the_United_States")
table = page[1]
state_data = table.iloc[:, np.r_[0:2, 6:7]]
state_data.to_csv("state_data.csv")

#some of the state names have extra character "D", needs to be removed
states = state_data.iloc[:,0].apply(lambda x: x.replace("[D]","")).tolist()
#abbreviations
state_abrevs = state_data.iloc[:,1].tolist()
###state sq miles
area = state_data.iloc[:,2].tolist()

#Census population data - *****the code scraping this is in the explore file*****
pop = pd.read_csv("population.csv")

#reshaping for easier lookup by state abbreviation
pop = pop.set_index('State')
pop = pop.drop(index=['District of Columbia','Puerto Rico'])
pop = pop.drop(columns='Unnamed: 0')
pop.insert(0, 'States', state_abrevs)
pop = pop.set_index('States')

#Abbreviations used by the API for coal, natural gas, petroleum, solar, wind, biomass, hydro, nuclear
resource_abrevs = ['CL','NG','PA','SO','WY','BM','HY','NU']
resource_names = ['Coal','Natural Gas','Petroleum','Solar','Wind','Biomass','Hydroelectricity','Nuclear']

#base url string for calling api
url_string = f"http://api.eia.gov/series/?api_key={api_key}&series_id=SEDS."

#this adds population to dataframe. to be used within call_api()
def add_pop(df):
    state = df.loc[0,'state']
    years = df['year'].tolist()
    population = []
    for year in years:
        rounded = (lambda x: x-(x%10))(int(year))
        census_pop = pop.loc[state][f'{rounded} Census']
        population.append(census_pop)
    return population

#This function will call the api and if successful will return a data frame for a single state/single resource
def call_api(state,resource):
    if resource == 'NU':
        series = f'{resource}ETB.{state}.A'
    else:
        series = f'{resource}TCB.{state}.A'
        
    request = requests.get(url_string+series)  
    if request.status_code == 200:
            response = request.json()
            data = response['series'][0]['data']
            df = pd.DataFrame(data,columns = ['year','usage'])
            df.insert(0,'state',state)
            df.insert(2,'resource',resource)
            population = add_pop(df)
            df.insert(3,'population',population)
            return df.dropna()
    else:
        print("Error: " + request.status_code + f" for {state} {resource}")

#insert data into state table
state_df = pd.DataFrame({'state_id':state_abrevs, 'state_name': states, 'area': area})
state_df.to_csv('state_table.csv',header=False,index=False)
state_table = csv.reader(open("state_table.csv"))
for row in state_table:
    cur.execute("INSERT INTO state_dim(state_id,state_name,area) VALUES(%s,%s,%s)",row)
mydb.commit()

resource_df = pd.DataFrame({'resource_id':resource_abrevs,'resource_name':resource_names,'unit_measurement':'BTU'})
resource_df.to_csv('resource_table.csv',header=False,index=False)
resource_table = csv.reader(open("resource_table.csv"))
for row in resource_table:
    cur.execute("INSERT INTO resource_dim(resource_id,resource_name,unit_measurement) VALUES(%s,%s,%s)",row)
mydb.commit()

#insert data into facts
for r in resource_abrevs:
    df = call_api(state_abrevs[0],r)
    for s in state_abrevs[1:]:
        df = pd.concat([df, call_api(s,r)]) 
    df.to_csv(f"{r}_data.csv",header=False,index=False)
    csv_data = csv.reader(open(f"{r}_data.csv"))
    for row in csv_data:
        cur.execute("INSERT INTO facts(state_id,year,resource_id,population,consumption) VALUES(%s,%s,%s,%s,%s)",row)
mydb.commit()


