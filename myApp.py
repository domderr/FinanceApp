import pandas as pd
import yfinance as yf
import datetime
from time import strftime,gmtime
import dash
from dash.dependencies import Input, Output
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_table.FormatTemplate as FormatTemplate
import plotly.graph_objs as go
import numpy as np

def refresh_data():
    d = {'Ticker': ['AAPL', 'MSFT','GOOG','AMZN','IBM'],
     'Name': ['Apple', 'Microsoft','Google','Amazon','Ibm']}

    list= pd.DataFrame(data=d)
    list['Name'] = list['Name'].str.slice(0,30)
    list_symbols=[]

    for symbol in list.Ticker:
        list_symbols.append(symbol)

    start="2015-1-1"
    end="2020-12-31"
    mylist= list_symbols

    df = yf.download(mylist, start=start,end=end,group_by='Ticker', interval='1D')
    df = df.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1)
    df['counter'] = df.groupby(['Ticker']).cumcount()
    df['NetCh']   = df.groupby('Ticker').Close.pct_change()
    
    dates=df.index
    df['Date']= dates.strftime('%Y-%m-%d')

    last_date_available=max(df.Date)
    table_df=df[df.Date==last_date_available]
    table_df=list.merge(table_df)
    
    return(list,df,table_df,last_date_available) 

list,df,table_df,last_date_available=refresh_data()

#app = dash.Dash(__name__)


app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

server = app.server

Ticker_options = []
for ticker in range(0,len(list)):
    Ticker_options.append({'label':list.Name.loc[ticker],'value':list.Ticker.loc[ticker]})
    
    
app.layout = html.Div([
    dcc.Tabs([
        
        dcc.Tab(html.Div([
              
                html.H1('Trading Analysis Dashboard'),
                html.H4('developed by Domenico DErrico - www.TradingAlgo.tech'),

                html.Div([
                    html.Button(
                        id='Refresh',
                        n_clicks=0,
                        children='Refresh',
                        style={'fontSize':12, 'marginLeft':'10px'}
                        ),
                    ], style={'display':'inline-block'}),
    

                    dash_table.DataTable(
                        id='datatable',
                            columns=[
                                {"name": 'Ticker', "id": 'Ticker'},
                                {"name": 'Name'  , "id": 'Name' },
                                {"name": 'NetCh' , "id": 'NetCh','type': 'numeric','format': FormatTemplate.percentage(2)},
                                {"name": 'Open'  , "id": 'Open', 'type': 'numeric','format': FormatTemplate.money(2)},
                                {"name": 'High'  , "id": 'High', 'type': 'numeric','format': FormatTemplate.money(2)},
                                {"name": 'Low'   , "id": 'Low',  'type': 'numeric','format': FormatTemplate.money(2)},
                                {"name": 'Close' , "id": 'Close','type': 'numeric','format': FormatTemplate.money(2)},
                                {"Name": 'Volume', "id": 'Volume',},
                                ]),

                    html.Div('last date available '+last_date_available),

                html.H5('NOTE: This App is for demonstration purpose only. Information made available is not an offer or solicitation of any kind in any jurisdiction '),

        ])),
        
        dcc.Tab(label='Chart', children=[
            
            html.Div([
              dcc.Dropdown(id='ticker-picker',
                           options=Ticker_options,
                           value=list.Ticker.iloc[0],
                           style={'color':'Black','padding':10,'width':1000,'height':50})
            ]),

            html.Div([
                 dcc.Graph(id='graph',
                           style={'color':'black', 'border':'2px black solid',
                                  'borderRadius':5,'padding':10, 'width':1800,'height':700}
            )])    
        ]),
    ])
])

@app.callback(
    Output('datatable', 'data'),
    [Input('Refresh', 'n_clicks')])
def update_table(n_clicks):
    list,df,table_df,today=refresh_data()
    data=table_df.to_dict('records')
    
    return(data)

@app.callback(Output('graph', 'figure'),
              [Input('ticker-picker', 'value')])
def update_figure(selected_ticker): 
    filtered_df = df[df['Ticker'] == selected_ticker]
    
    trace0=go.Bar(
            x=filtered_df.index,
            y=filtered_df.Close,
            xaxis="x",
            yaxis="y",
            visible=True,
            showlegend=False,
            opacity=0,
            #hovertext=df.index
            hoverinfo="none",
    )
    
    
    trace1=go.Candlestick(
            x=filtered_df.counter,
            open=filtered_df.Open,
            high=filtered_df.High,
            low=filtered_df.Low,
            close=filtered_df.Close,
            xaxis="x2",
            yaxis="y",
            visible=True,
            showlegend=False,
            opacity=1,
            #hoverinfo="none",
            hovertext=filtered_df.index.strftime("%D"),
            #name="last:"+str(df.Close.iloc[-1])
    )
    
    trace2 = go.Bar(
        x=filtered_df.counter,
        y=filtered_df.Volume,
        xaxis="x2",
        yaxis="y2",
        name="Volume",
        marker_color='Green', 
        marker_line_color='Green', 
        marker_line_width=1, 
        opacity=0.6
    )
    
    
       
    data=[trace0,trace1,trace2]
    
    layout=go.Layout(
        title=go.layout.Title(text=selected_ticker),
        autosize=True,
        #width=500,
        #height=500,
        xaxis=go.layout.XAxis(
            side="bottom",
            showticklabels=True,
            tickformat = '%Y-%m-%d',
            showgrid = True
            
        ),
        yaxis=go.layout.YAxis(
            side="right",
            range=[min(filtered_df.Low)*.99, max(filtered_df.High)*1.01],# margini verticali
            showticklabels=True,
            showgrid = True,
            domain=[0.30, 1]
        ),
        xaxis2=go.layout.XAxis(
            side="top",
            showticklabels=False,
            rangeslider=go.layout.xaxis.Rangeslider(visible=False),
            showgrid = True,
            tickformat = '%Y-%m-%d',
        ),
        yaxis2=go.layout.YAxis(
            side="right",
            #range=[min(filtered_df.Volume)*.99, max(filtered_df.Volume)*1.01],# margini verticali
            showticklabels=False,
            showgrid = True,
            domain=[0, 0.25]
        ),
        plot_bgcolor ='White'
    )
        
        
    return { 'data': data,'layout': layout}
 
    
if __name__ == '__main__':
    app.run_server()
