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
dfm = pd.DataFrame({'word': ['climate', 'emission', 'esg', 'investment', 'energy', 'initiative', 'management', 'sustainability'], 
                    'freq': [20, 18, 16, 14, 11, 8, 7, 4]})
def plot_wordcloud(data):
    d = {a: x for a, x in data.values}
    wc = WordCloud(background_color='white', width=480, height=400)
    wc.fit_words(d)
    return wc.to_image()

# For decarbonization rating
ratings_file = pd.read_csv('data/all_percentile.csv', usecols=['name', 'percentile'])

# For sentiment 
sentiment_file = pd.read_csv('data/sentiment_dummy.csv', usecols=['Company', 'Sentiment'])

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
                                style={'height':250},
                                showCurrentValue=True
                        ),
                    ])
                ], color='light', outline=True)     

card_decarbonization_ratings = dbc.Card([
                                    dbc.CardBody([
                                        html.H5('Decarbonisation Ratings', className='text-center'),
                                        html.H1(id='decarbonization_rating', children='', className='text-center text-success'), 
                                        html.P('Out of 100', className='text-center')
                                    ]),
                                ], color='light', outline=True)

card_initiative_count = dbc.Card([
                            dbc.CardBody([
                                html.H5('Actively Participating In', className='text-center'),
                                html.H1(id='initiative_count', children='', className='text-center text-success'),
                                html.P('Global Initiatives', className='text-center')
                            ]),
                        ], color='light', outline=True)

card_initiatives = dbc.Card([
                        dbc.CardBody([
                            html.H5('Global Initiatives', className='text-center'),
                            dcc.Graph(id='initiative_table', figure={})
                        ])
                    ])

card_wordcloud = dbc.Card([
                    dbc.CardBody([
                        html.H5('WordCloud', className='text-center'),
                        html.Br(),
                        dbc.CardImg(id='word_cloud', className='mx-auto')
                    ])
                ], className='card h-100')
                                
# Layout -----------------------------------------------------------------------------
app.layout = dbc.Container([
    # Declare rows: 4 Rows
    # Row 1: For Header and dropdown
    dbc.Row([
        dbc.Col(html.H1('Decarbonization Dashboard',
                        className='text-center mb-4'),
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

    # Row 3: For Sentiment Gauge Chart, Big Number, BoxPlot
    dbc.Row([
        dbc.Col([card_sentiment], width={'size':3, 'offset':0, 'order':1}),
        dbc.Col([
            card_decarbonization_ratings,
            html.Br(),
            card_initiative_count
        ], width={'size':3, 'offset':0, 'order':2}),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5('Benchmark Comparison', className='text-center'), 
                    dcc.Graph(id='bulletplot', figure={})
                ])
            ])
        ], width={'size':6, 'offset':0, 'order':3})
    ]),

    html.Br(),
    
    # Row 4: For Global Initiatives Table & WordCloud
    dbc.Row([
        dbc.Col([card_initiatives], width={'size':7, 'offset':0, 'order':1}),
        dbc.Col([card_wordcloud], width={'size':5, 'offset':0, 'order':2})
    ])
], fluid=True)

# Callback -----------------------------------------------------------------------------
# For Sentiment Gauge Chart
@app.callback(
    Output(component_id='sentiment_gauge', component_property='value'),
    Input(component_id='company_dropdown', component_property='value')
)
def update_output(company):
    sentiment = sentiment_file.set_index('Company').Sentiment.loc[company]
    return sentiment

# For Big Numbers 1: Decarbonization Rating
@app.callback(
    Output(component_id='decarbonization_rating', component_property='children'),
    Input(component_id='company_dropdown', component_property='value')
    )
def update_output(company):
    rating = round(ratings_file.set_index('name').percentile.loc[company])
    return rating

# For Big Numbers 2: Initiative Count
@app.callback(
    Output(component_id='initiative_count', component_property='children'),
    Input(component_id='company_dropdown', component_property='value')
    )
def update_output(company):
    company_initiative = all_initiative_array.set_index('Company').Initiatives.loc[company]
    count = len(ast.literal_eval(company_initiative))
    return count

# For Bullet Plot
@app.callback(
    Output(component_id='bulletplot', component_property='figure'),
    Input(component_id='company_dropdown', component_property='value')
    )
def update_graph(company):
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode = "gauge", 
        value = round(ratings_file.set_index('name').percentile.loc[company]),
        domain = {'x': [0.25, 1], 'y': [0.08, 0.25]},
        title = {'text': "Decarbonization Rating"},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 25], 'color': "#F25757"}, # 25th percentile
                {'range': [25, 50], 'color': "#FFC15E"}, # 50th percentile
                {'range': [50, 75], 'color': "#F5FF90"}, # 75th percentile
                {'range': [75, 100], 'color': "#D6FFB7"}], # 100th percentile
            'bar': {'color': "black"}}))

    fig.add_trace(go.Indicator(
        mode = "gauge", 
        value = len(ast.literal_eval(all_initiative_array.set_index('Company').Initiatives.loc[company])),
        domain = {'x': [0.25, 1], 'y': [0.4, 0.6]},
        title = {'text': "Initiative Count"},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [None, 10]},
            'steps': [
                {'range': [0, 3], 'color': "#F25757"}, # 25th percentile
                {'range': [3, 4], 'color': "#FFC15E"}, # 50th percentile
                {'range': [4, 6], 'color': "#F5FF90"}, # 75th percentile
                {'range': [6, 10], 'color': "#D6FFB7"}], # 100th percentile
            'bar': {'color': "black"}}))

    fig.add_trace(go.Indicator(
        mode = "gauge", 
        value = sentiment_file.set_index('Company').Sentiment.loc[company], #company's score
        domain = {'x': [0.25, 1], 'y': [0.7, 0.9]},
        title = {'text' :"Overall Sentiment"},
        gauge = {
            'shape': "bullet",
            'axis': {'range': [None, 5]}, # 0 to 5
            'steps': [ 
                {'range': [0, 2.1], 'color': "#F25757"}, # 25th percentile
                {'range': [2.1, 3.4], 'color': "#FFC15E"}, # 50th percentile
                {'range': [3.4, 4.2], 'color': "#F5FF90"}, # 75th percentile
                {'range': [4.2, 5], 'color': "#D6FFB7"}], # 100th percentile
            'bar': {'color': "black"}}))

    fig.update_layout(height = 250 , margin = {'t':0, 'b':0})
    fig.update_traces(title_font_size=12, gauge_bar_thickness=0.3)
    return fig

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