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
import dash_bootstrap_components as dbc 
import dash_daq as daq

from io import BytesIO
from wordcloud import WordCloud
import base64

# Bootstrap --------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
                )

# Load Data --------------------------------------------------------------------------

# Load company names to display in dropdown menu
companylabels = pd.read_csv('data/companylabels.csv', usecols=['FullName', 'ShortForm'])
companylabels = companylabels.values.tolist()

# For global initiatives table 
initiatives_file = pd.read_csv('data/esg_initiatives.csv')
# replace NaN for initiatives without acronym
initiatives_file = initiatives_file.replace({np.nan: '-'})
# dictionary: key-initiative spelled out fully, value-[acronym, description]
initiatives_dict = initiatives_file.set_index('Initiative').T.to_dict('list')
# read csv containing all initiatives
all_initiative_array = pd.read_csv('data/all_initiatives.csv')

# For WordCloud
dfm = pd.DataFrame({'word': ['climate', 'emission', 'esg', 'investment', 'energy'], 'freq': [10, 8, 6, 4, 1]})
def plot_wordcloud(data):
    d = {a: x for a, x in data.values}
    wc = WordCloud(background_color='white', width=480, height=360)
    wc.fit_words(d)
    return wc.to_image()

# For decarbonization rating
ratings_file = pd.read_csv('data/all_percentile.csv', usecols=['name', 'percentile'])

# Cards --------------------------------------------------------------------------------
card_sentiment = dbc.Card([
                    dbc.CardBody([
                        html.H5('Overall Sentiment Level', className='text-center'),
                        daq.Gauge(id='sentiment_gauge',
                                color={"gradient":True,"ranges":{"red":[0,3],"yellow":[3,4],"green":[4,5]}},
                                value=3.6,
                                max=5,
                                min=0,
                                className='d-flex justify-content-center',
                                style={'height':200}
                        )
                    ])
                ])     

card_decarbonization_ratings = dbc.Card([
                                    dbc.CardBody([
                                        html.H5('Decarbonisation Ratings'),
                                        html.H1(id='decarbonization_rating', children='')
                                    ]),
                                ], color='success', outline=True)

                                
# Layout -----------------------------------------------------------------------------
app.layout = dbc.Container([
    # Declare rows: 4 Rows
    # Row 1: For Header and dropdown
    dbc.Row([
        dbc.Col(html.H1('Decarbonization Dashboard',
                        className='text-center, mb-4'),
                width=12)
    ]),

    # Row 2: For Dropdown
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='company_dropdown',
                        options=[{'label': x[0], 'value': x[1]} for x in companylabels],
                        multi=False,
                        value='AXA')
        ], width={'size':5})
    ]),

    html.Br(),
    html.Br(),

    # Row 3: For Sentiment Gauge Chart, Big Number, BoxPlot
    dbc.Row([
        dbc.Col([card_sentiment], width={'size':3, 'offset':0, 'order':1}),
        dbc.Col([card_decarbonization_ratings], width={'size':3, 'offset':0, 'order':2}),
        dbc.Col([
            dcc.Graph(id='boxplot', figure={})
        ], width={'size':6, 'offset':0, 'order':3})
    ]),

    # Row 4: For Global Initiatives Table & WordCloud
    dbc.Row([
        dbc.Col([
            html.H5('Global Initiatives', className='text-center'),
            dcc.Graph(id='initiative_table', figure={})
        ], width={'size':7, 'offset':0, 'order':1}),
        dbc.Col([
            html.H5('WordCloud', className='text-center'),
            dbc.CardImg(id='word_cloud')
        ], width={'size':5, 'offset':0, 'order':2})
    ])
], fluid=True)

# Callback -----------------------------------------------------------------------------
# For Sentiment Gauge Chart
@app.callback(
    Output(component_id='sentiment_gauge', component_property='value'),
    Input(component_id='company_dropdown', component_property='value')
)
def update_output(value):
    return value # !! need to change according to company

# For Big Numbers 1: Decarbonization Rating
@app.callback(
    Output(component_id='decarbonization_rating', component_property='children'),
    Input(component_id='company_dropdown', component_property='value')
    )
def update_output(company):
    rating = round(ratings_file.set_index('name').percentile.loc[company])
    return rating
    

# Global Initiatives Table
@app.callback(
    Output(component_id='initiative_table', component_property='figure'),
    Input(component_id='company_dropdown', component_property='value')
)
def update_graph(option_slctd):
    company_initiative = all_initiative_array.set_index('Company').Initiatives.loc[option_slctd]
    company_initiative = ast.literal_eval(company_initiative)
    company_initiative = sorted(company_initiative)
    
    data = []
    for full_name in company_initiative:
        acronym = initiatives_dict[full_name][0]
        details = initiatives_dict[full_name][1]  
        data.append([full_name, acronym, details])
    
    df = pd.DataFrame(data, columns = ['Initiatives', 'Acronym', 'Details'])

    fig = go.Figure(data=[go.Table(
        columnwidth = [100, 50, 400],
        header = dict(
            values=list(df.columns),
            font_color='rgb(100,100,100)',
            fill_color='aquamarine',
            align='left'),
        cells = dict(
            values=[df.Initiatives, df.Acronym, df.Details],
            fill_color='white', 
            font_color='rgb(100,100,100)',
            font_size=10,
            align='left',
            height=20)),
    ], layout=go.Layout(margin={'l':0, 'r':0, 't':10, 'b':10}))

    return fig

# For WordCloud
@app.callback(
    Output(component_id='word_cloud', component_property='src'),
    Input(component_id='company_dropdown', component_property='value')
)
def make_image(option_slctd):
    img = BytesIO()
    plot_wordcloud(data=dfm).save(img, format='PNG')  # !! need to change according to company
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())

# -------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)