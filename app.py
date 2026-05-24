"""
NYC Airbnb Listings — Interactive Dashboard
Capstone Project | Data Analysis with AI
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import os

def load_data():
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'listings.csv')
    df = pd.read_csv(csv_path, low_memory=False)
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df[df['price'].notna() & (df['price'] > 0)]
    df['price'] = df['price'].clip(upper=1000)
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
    return df

df = load_data()

BOROUGHS   = sorted(df['neighbourhood_group'].unique())
ROOM_TYPES = sorted(df['room_type'].unique())
PRICE_MAX  = int(df['price'].quantile(0.99))

BOROUGH_CLR = {
    'Manhattan':    '#1F5F8A',
    'Brooklyn':     '#2E8B57',
    'Queens':       '#BA7517',
    'Bronx':        '#993556',
    'Staten Island':'#5F5E5A',
}
ROOM_CLR = {
    'Entire home/apt': '#1F5F8A',
    'Private room':    '#2E8B57',
    'Shared room':     '#BA7517',
    'Hotel room':      '#993556',
}

app = Dash(
    __name__,
    title="NYC Airbnb Dashboard",
    suppress_callback_exceptions=True
)
server = app.server

CARD  = {'background':'#fff','border':'1px solid #e8ecf0','borderRadius':'10px',
         'padding':'16px 18px','marginBottom':'14px'}
KCARD = {'background':'#EEF4FB','borderRadius':'8px','padding':'14px 10px','textAlign':'center'}

def kpi_card(label, val_id):
    return html.Div([
        html.Div(id=val_id, style={'fontSize':'24px','fontWeight':'700','color':'#1F5F8A'}),
        html.Div(label, style={'fontSize':'10px','color':'#888','marginTop':'3px',
                               'textTransform':'uppercase','letterSpacing':'0.06em'}),
    ], style=KCARD)

app.layout = html.Div([

    html.Div([
        html.H1("NYC Airbnb Dashboard",
                style={'margin':'0','fontSize':'20px','fontWeight':'700','color':'#1F5F8A'}),
        html.Div("Capstone Project · Data Analysis with AI · Inside Airbnb",
                 style={'fontSize':'11px','color':'#aaa','marginTop':'2px'}),
    ], style={'background':'#fff','borderBottom':'1px solid #eee','padding':'14px 20px'}),

    html.Div([

        # Sidebar
        html.Div([
            html.Div([
                html.Div("FILTERS", style={'fontSize':'10px','fontWeight':'700',
                                           'color':'#bbb','letterSpacing':'0.1em','marginBottom':'12px'}),
                html.Label("Borough", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(id='f-borough',
                    options=[{'label':b,'value':b} for b in BOROUGHS],
                    multi=True, placeholder="All boroughs",
                    style={'fontSize':'12px','marginBottom':'14px','marginTop':'3px'}),
                html.Label("Room type", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(id='f-room',
                    options=[{'label':r,'value':r} for r in ROOM_TYPES],
                    multi=True, placeholder="All room types",
                    style={'fontSize':'12px','marginBottom':'14px','marginTop':'3px'}),
                html.Label("Price ($/night)", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.RangeSlider(id='f-price', min=0, max=PRICE_MAX, step=10,
                    value=[0, PRICE_MAX],
                    marks={0:'$0', 200:'$200', 500:'$500', PRICE_MAX:f'${PRICE_MAX}+'},
                    tooltip={'placement':'bottom','always_visible':False}),
                html.Div(style={'marginBottom':'14px'}),
                html.Label("Availability", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(id='f-avail',
                    options=[{'label':'Any','value':'any'},
                             {'label':'High 180+ days','value':'high'},
                             {'label':'Low <60 days','value':'low'}],
                    value='any', clearable=False,
                    style={'fontSize':'12px','marginBottom':'14px','marginTop':'3px'}),
                html.Div(id='f-count', style={'fontSize':'11px','color':'#999','marginTop':'8px'}),
            ], style=CARD),
        ], style={'width':'200px','flexShrink':'0'}),

        # Main
        html.Div([
            html.Div([
                kpi_card("Listings",         'kpi-n'),
                kpi_card("Median $/night",   'kpi-price'),
                kpi_card("Avg avail (days)", 'kpi-avail'),
                kpi_card("Reviews/mo",       'kpi-rev'),
                kpi_card("Multi-host %",     'kpi-multi'),
            ], style={'display':'grid','gridTemplateColumns':'repeat(5,1fr)',
                      'gap':'10px','marginBottom':'14px'}),

            html.Div([
                html.Div([
                    html.Div("Median price by borough",
                             style={'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'6px'}),
                    dcc.Graph(id='g-bar', style={'height':'300px'},
                              config={'displayModeBar':False},
                              figure=go.Figure()),
                ], style={**CARD,'flex':'1','marginBottom':'0'}),
                html.Div([
                    html.Div("Room type share",
                             style={'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'6px'}),
                    dcc.Graph(id='g-donut', style={'height':'300px'},
                              config={'displayModeBar':False},
                              figure=go.Figure()),
                ], style={**CARD,'flex':'1','marginBottom':'0'}),
            ], style={'display':'flex','gap':'12px','marginBottom':'14px'}),

            html.Div([
                html.Div([
                    html.Div("Review activity over time",
                             style={'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'6px'}),
                    dcc.Graph(id='g-ts', style={'height':'260px'},
                              config={'displayModeBar':False},
                              figure=go.Figure()),
                ], style={**CARD,'flex':'2','marginBottom':'0'}),
                html.Div([
                    html.Div("Availability distribution",
                             style={'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'6px'}),
                    dcc.Graph(id='g-avail-hist', style={'height':'260px'},
                              config={'displayModeBar':False},
                              figure=go.Figure()),
                ], style={**CARD,'flex':'1','marginBottom':'0'}),
            ], style={'display':'flex','gap':'12px','marginBottom':'14px'}),

            html.Div([
                html.Div("Price distribution",
                         style={'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'6px'}),
                dcc.Graph(id='g-hist', style={'height':'200px'},
                          config={'displayModeBar':False},
                          figure=go.Figure()),
            ], style={**CARD,'marginBottom':'0'}),

        ], style={'flex':'1','minWidth':'0'}),

    ], style={'display':'flex','gap':'14px','padding':'14px 20px',
              'backgroundColor':'#f7f8fa','minHeight':'calc(100vh - 54px)',
              'fontFamily':'Helvetica Neue, Arial, sans-serif'}),

], style={'backgroundColor':'#f7f8fa'})


@app.callback(
    Output('kpi-n',       'children'),
    Output('kpi-price',   'children'),
    Output('kpi-avail',   'children'),
    Output('kpi-rev',     'children'),
    Output('kpi-multi',   'children'),
    Output('f-count',     'children'),
    Output('g-bar',       'figure'),
    Output('g-donut',     'figure'),
    Output('g-ts',        'figure'),
    Output('g-avail-hist','figure'),
    Output('g-hist',      'figure'),
    Input('f-borough',    'value'),
    Input('f-room',       'value'),
    Input('f-price',      'value'),
    Input('f-avail',      'value'),
)
def update(boroughs, rooms, price_range, avail):
    dff = df.copy()
    if boroughs:
        dff = dff[dff['neighbourhood_group'].isin(boroughs)]
    if rooms:
        dff = dff[dff['room_type'].isin(rooms)]
    if price_range:
        dff = dff[(dff['price'] >= price_range[0]) & (dff['price'] <= price_range[1])]
    if avail == 'high':
        dff = dff[dff['availability_365'] >= 180]
    elif avail == 'low':
        dff = dff[dff['availability_365'] < 60]

    n = len(dff)

    BL = dict(
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=40, r=20, t=20, b=40),
        font=dict(family='Arial', size=12, color='#333')
    )

    def empty():
        f = go.Figure()
        f.update_layout(**BL)
        f.add_annotation(text="No data", xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False,
                         font=dict(color="#bbb", size=14))
        return f

    if n == 0:
        e = empty()
        return "0","—","—","—","—","0 listings",e,e,e,e,e

    kn  = f"{n:,}"
    kp  = f"${dff['price'].median():.0f}"
    ka  = f"{dff['availability_365'].mean():.0f}"
    kr  = f"{dff['reviews_per_month'].mean():.2f}"
    km  = f"{(dff['calculated_host_listings_count']>1).mean()*100:.1f}%"
    fc  = f"{n:,} listings"

    # Bar
    bd = dff.groupby('neighbourhood_group')['price'].median().sort_values().reset_index()
    g_bar = go.Figure(go.Bar(
        y=bd['neighbourhood_group'],
        x=bd['price'],
        orientation='h',
        marker_color=[BOROUGH_CLR.get(b,'#888') for b in bd['neighbourhood_group']],
        text=[f"${v:.0f}" for v in bd['price']],
        textposition='outside'
    ))
    g_bar.update_layout(**BL,
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False,
                   tickprefix='$', title='Median price ($)'),
        yaxis=dict(showgrid=False),
        bargap=0.3)

    # Donut
    rc = dff['room_type'].value_counts().reset_index()
    rc.columns = ['room_type','count']
    g_donut = go.Figure(go.Pie(
        labels=rc['room_type'],
        values=rc['count'],
        hole=0.5,
        marker_colors=[ROOM_CLR.get(r,'#aaa') for r in rc['room_type']],
        textinfo='percent+label',
        textfont_size=12
    ))
    g_donut.update_layout(**BL, showlegend=False)

    # Time series
    ts = dff[dff['last_review'].notna()].copy()
    ts['ym'] = ts['last_review'].dt.to_period('M').dt.to_timestamp()
    mo = ts.groupby('ym').size().reset_index(name='cnt')
    mo = mo[mo['ym'] >= '2015-01-01']
    g_ts = go.Figure()
    if len(mo) > 1:
        g_ts.add_trace(go.Scatter(
            x=mo['ym'], y=mo['cnt'], mode='lines',
            line=dict(color='#1F5F8A', width=2.5),
            fill='tozeroy', fillcolor='rgba(31,95,138,0.12)',
            name='Reviews'
        ))
    g_ts.update_layout(**BL,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0',
                   zeroline=False, title='Reviews/month'),
        showlegend=False)

    # Availability histogram
    g_avail_hist = go.Figure(go.Histogram(
        x=dff['availability_365'], nbinsx=30,
        marker_color='#2E8B57',
        marker_line_color='white', marker_line_width=0.5
    ))
    g_avail_hist.update_layout(**BL,
        xaxis=dict(title='Days available/year', showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False),
        bargap=0.05)

    # Price histogram
    g_hist = go.Figure(go.Histogram(
        x=dff['price'], nbinsx=50,
        marker_color='#1F5F8A',
        marker_line_color='white', marker_line_width=0.4
    ))
    mp = dff['price'].median()
    g_hist.add_vline(x=mp, line_dash='dash', line_color='#BA7517', line_width=2,
        annotation_text=f'Median ${mp:.0f}',
        annotation_position='top right',
        annotation_font_color='#BA7517', annotation_font_size=11)
    g_hist.update_layout(**BL,
        xaxis=dict(title='Price/night ($)', tickprefix='$',
                   showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False),
        bargap=0.04)

    return kn,kp,ka,kr,km,fc, g_bar,g_donut,g_ts,g_avail_hist,g_hist


if __name__ == '__main__':
    app.run(debug=True, port=8050)
