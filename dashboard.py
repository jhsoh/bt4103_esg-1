import pandas as pd
import plotly.express as px  
import numpy as np
import ast
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash(__name__)

# -- Import and clean data (importing csv into pandas)--------------------------
#initiatives_file = pd.read_excel('data/ESG_Initiatives.xlsx', usecols="A,B,C")
initiatives_file = pd.read_csv('data/esg_initiatives.csv')

# replace NaN for initiatives without acronym
initiatives_file = initiatives_file.replace({np.nan: '-'})

# dictionary: key-initiative spelled out fully, value-[acronym, description]
initiatives_dict = initiatives_file.set_index('Initiative').T.to_dict('list')

all_initiative_array = pd.read_csv('data/insurance_initiatives.csv') # change path according to FI
all_initiative_array = all_initiative_array.drop(all_initiative_array.columns[0], axis=1)

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Decarbonisation Dashboard", style={'text-align': 'center'}),
    #Testing
    html.Div(id='output_container', children=[]),
    html.Br(),
    dcc.Dropdown(id="company",
                 options=[
                     {"label": "AXA", "value": "AXA"},
                     {"label": "AIA", "value": "AIA"},
                     {"label": "Cathay Life Insurance", "value": "Cathay"},
                     {"label": "Dai-ichi Life Insurance", "value": "DaiichiLife"},
                     {"label": "Shinkong Insurance", "value": "ShinKong"},
                     {"label": "Sun Life", "value": "SunLife"},
                     {"label": "Ping An Insurance", "value": "PingAn"},
                     {"label": "Japan Post Insurance", "value": "JapanPost"},
                     {"label": "Prudential", "value": "Prudential"},
                     {"label": "Mitsubishi UFJ Financial Group", "value": "MUFG"},
                     {"label": "FWD Insurance", "value": "FWD"},
                     {"label": "Nippon Life Insurance", "value": "NipponLife"},
                     {"label": "Asahi Mutual Life Insurance Company", "value": "AsahiMutual"},
                     {"label": "Kyobo Life Insurance", "value": "Kyobo"},
                     {"label": "Meiji Yasuda Life", "value": "MeijiYasuda"},
                     {"label": "Tokio Marine Holdings", "value": "TokioMarine"},
                     {"label": "KB Financial Group", "value": "KBFG"},
                     {"label": "Fukoku Mutual Life Insurance Company", "value": "Fukoku"},
                     {"label": "DGB Life Insurance", "value": "DGB"},
                     {"label": "Government Pension Investment Fund (Japan)", "value": "GPIF"},
                     {"label": "Taiwan Life Insurance ", "value": "TaiwanLife"},
                     {"label": "Nan Shan Life Insurance ", "value": "NanShanLife"}],
                 multi=False,
                 value="AXA",
                 style={'width': "40%"}
                 ),

    dcc.Graph(id='initiative_table', figure={})

])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='initiative_table', component_property='figure')],
    [Input(component_id='company', component_property='value')]
)
def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))

    container = "Select Company"

    company_initiative = ast.literal_eval(all_initiative_array.loc[all_initiative_array['Company'] == option_slctd]['Initiatives'].item())
    company_initiative = sorted(company_initiative)

    data = []
    for full_name in company_initiative:
        acronym = initiatives_dict[full_name][0]
        details = initiatives_dict[full_name][1]  
        data.append([full_name, acronym, details])
    
    df = pd.DataFrame(data, columns = ['Initiatives', 'Acronym', 'Details'])
    rows = len(df.index)

    fig = go.Figure(data=[go.Table(
        columnwidth = [130, 30, 380],
        header = dict(
            values=list(df.columns),
            font_color='rgb(100,100,100)',
            fill_color='aquamarine',
            align='left'),
        cells = dict(
            values=[df.Initiatives, df.Acronym, df.Details],
            # 2-D list of colors for alternating rows
            fill_color='white', 
            font_color='rgb(100,100,100)',
            font_size=10,
            align='left',
            height=20))
    ])

    return container, fig


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)