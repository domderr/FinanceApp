# Developed by Domenico D'Errico - www.tradingalgo.tech 
# Dec 19 - 2020



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
    d = {'Ticker': ['SPY', 'QQQ','DIA','IWN','XLB','XLE','XLF','XLI','XLK','XLP','XLU','XLY','XLV'],
     'Name': ['S&P 500', 'Nasdaq','DowJones','Russel','Basic Materials','Energy','Financials','Industrials','Tecnology',
             'Staples','Utilities','Discretionay','Health Care']}

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

app = dash.Dash(__name__)
server = app.server

Ticker_options = []
for ticker in range(0,len(list)):
    Ticker_options.append({'label':list.Name.loc[ticker],'value':list.Ticker.loc[ticker]})
    
    
app.layout = html.Div([
      
    html.Div([
        html.H1('Trading Analysis Dashboard'),
        html.H4('developed by Domenico DErrico - www.TradingAlgo.tech'),

        html.Button(
            id='Refresh',
            n_clicks=0,
            children='Refresh',
            style={'fontSize':12, 'marginLeft':'10px'}),

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
                ],
            row_selectable="single",
            selected_rows=[0],
            
            fixed_rows={'headers': True},
                   
            style_cell_conditional=[
                        {'if': {'column_id': 'Ticker'},'textAlign': 'left' ,'width': 30},
                        {'if': {'column_id': 'Name'},  'textAlign': 'left' ,'width': 80},
                        {'if': {'column_id': 'NetCh'}, 'textAlign': 'right' ,'width': 10},
                        {'if': {'column_id': 'Open'},  'textAlign': 'right','width': 80},
                        {'if': {'column_id': 'High'},  'textAlign': 'right','width': 80},
                        {'if': {'column_id': 'Low'},   'textAlign': 'right','width': 80},
                        {'if': {'column_id': 'Close'}, 'textAlign': 'right','width': 80},
                        {'if': {'column_id': 'Volume'},'textAlign': 'right','width': 80},

                        {'if': {'filter_query': '{NetCh} < 0',  # matching rows of a hidden column with the id, `id`
                                'column_id': 'NetCh'},'color': 'Red'}],
            
            filter_action='native',
            sort_action='native',
            page_action='none',
            style_table={'height': '300px', 'overflowY': 'auto'}            
        )
    ],style={'display':'inline-block', 'verticalAlign':'top', 'width':'100%','height':'50%'}),
        
    html.Div([
        html.Div([
            #html.H3('Select start and end dates:'),
            dcc.DatePickerRange(
                id='my_date_picker',
                min_date_allowed=datetime.datetime(2010, 1, 1),
                max_date_allowed=datetime.datetime.today(),
                start_date=datetime.datetime(2020, 1, 1),
                end_date=datetime.datetime.today()
            )],style={'display':'inline', 'verticalAlign':'top', 'width':'20%'}),
        
        html.Div([
            dcc.Graph(id='graph',
               style={'color':'black', 'border':'2px black solid','borderRadius':5},
               config={'displayModeBar': False})
                ],style={'display':'inline-block', 'verticalAlign':'top', 'width':'100%','scrollZoom': 'false'}),  
        
            
        
    
    ],style={'display':'inline-block', 'verticalAlign':'top', 'width':'100%','height':'50%','overflowX':'scroll'})

])


@app.callback(
    Output('datatable', 'data'),
    [Input('Refresh', 'n_clicks')])
def update_table(n_clicks):
    list,df,table_df,today=refresh_data()
    data=table_df.to_dict('records')
    
    return(data)   

@app.callback(
    Output('graph', 'figure'),
    [Input('datatable', "derived_virtual_data"),
     Input('datatable', "selected_rows"),
     Input('my_date_picker', 'start_date'),
     Input('my_date_picker', 'end_date')]
)
def update_figure(rows, derived_virtual_selected_rows,start_date,end_date):

    posizione_Ticker_selezionato=derived_virtual_selected_rows[0]
    selected_ticker=list['Ticker'][list.index[derived_virtual_selected_rows[0]]]
    
    filtered_df = df[(df.Ticker==selected_ticker)&(df.index >= start_date)&(df.index <= end_date)]
    
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
        margin=go.layout.Margin(
            l=50, #left margin
            r=50, #right margin
            b=50, #bottom margin
            t=50 #top margin
        ),
        
        xaxis=go.layout.XAxis(
            side="bottom",
            showticklabels=True,
            tickformat = '%Y-%m-%d',
            showgrid = True,
            fixedrange=True
            
        ),
        yaxis=go.layout.YAxis(
            side="right",
            range=[min(filtered_df.Low)*.99, max(filtered_df.High)*1.01],# margini verticali
            showticklabels=True,
            showgrid = True,
            domain=[0.30, 1],
            fixedrange=True
        ),
        xaxis2=go.layout.XAxis(
            side="top",
            showticklabels=False,
            rangeslider=go.layout.xaxis.Rangeslider(visible=False),
            showgrid = True,
            tickformat = '%Y-%m-%d',
            fixedrange=True
        ),
        yaxis2=go.layout.YAxis(
            side="right",
            #range=[min(filtered_df.Volume)*.99, max(filtered_df.Volume)*1.01],# margini verticali
            showticklabels=False,
            showgrid = True,
            domain=[0, 0.25],
            fixedrange=True
        ),
        plot_bgcolor ='White'
    )
        
        
    return { 'data': data,'layout': layout}

if __name__ == '__main__':
    app.run_server()
