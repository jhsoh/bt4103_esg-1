import pandas as pd
import plotly.express as px  
import numpy as np
import ast
import plotly as py
import plotly.graph_objects as go
import random

import dash
import dash_core_components as dcc
import dash.dependencies as dd
import dash_html_components as html
from dash.dependencies import Input, Output

from io import BytesIO

from wordcloud import WordCloud
import base64


app = dash.Dash(__name__)

# -- Import and clean data (importing csv into pandas)--------------------------

### Load company names to display in dropdown menu
companylabels = pd.read_csv('data/companylabels.csv', usecols=['FullName', 'ShortForm'])
companylabels = companylabels.values.tolist()

### For global initiatives table 
initiatives_file = pd.read_csv('data/esg_initiatives.csv')

# replace NaN for initiatives without acronym
initiatives_file = initiatives_file.replace({np.nan: '-'})

# dictionary: key-initiative spelled out fully, value-[acronym, description]
initiatives_dict = initiatives_file.set_index('Initiative').T.to_dict('list')

# combine all initiatives from 4 FIs into one dataframe
ab_initiatives = pd.read_csv('data/asian_banks_initiatives.csv')
as_initiatives = pd.read_csv('data/asset_managers_initiatives.csv')
ins_initiatives = pd.read_csv('data/insurance_initiatives.csv')
pf_initiatives = pd.read_csv('data/pension_funds_initiatives.csv')
all_initiative_array = pd.concat([ab_initiatives, as_initiatives, ins_initiatives, pf_initiatives])
all_initiative_array = all_initiative_array.drop(all_initiative_array.columns[0], axis=1)
all_initiative_array = all_initiative_array.reset_index(drop=True)

### For word cloud
dfm = pd.DataFrame({'word': ['apple', 'pear', 'orange'], 'freq': [1,3,9]})

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Decarbonisation Dashboard", style={'text-align': 'center'}),

    html.Div(id='output_container', children=[]),
    html.Br(),
    dcc.Dropdown(id="company",
                 options=[{'label': x[0], 'value': x[1]} for x in companylabels],
                 multi=False,
                 value="AXA",
                 style={'width': "50%"}
                 ),

    dcc.Graph(id='initiative_table', figure={}),
    html.Div([html.Img(id="image_wc")])

])


# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='initiative_table', component_property='figure')],
    [Input(component_id='company', component_property='value')]
)
def update_graph(option_slctd):
    print(option_slctd) # for checking
    print(type(option_slctd)) # for checking

    container = "Select Company"

    company_initiative = all_initiative_array.set_index('Company').Initiatives.loc[option_slctd]
    company_initiative = ast.literal_eval(company_initiative)
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

def plot_wordcloud(data):
    d = {a: x for a, x in data.values}
    wc = WordCloud(background_color='black', width=480, height=360)
    wc.fit_words(d)
    return wc.to_image()

@app.callback(dd.Output('image_wc', 'src'), [dd.Input('image_wc', 'id')])
def make_image(b):
    img = BytesIO()
    plot_wordcloud(data=dfm).save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)