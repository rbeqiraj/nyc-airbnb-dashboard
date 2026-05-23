"""
NYC Airbnb Listings — Interactive Dashboard
Capstone Project | Data Analysis with AI

Run locally:   python app.py
Deploy:        See README.md for Render / Hugging Face instructions
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback
import urllib.request
import os

# ── Data loading ──────────────────────────────────────────────────────────────
DATA_URL  = "https://data.insideairbnb.com/united-states/ny/new-york-city/2024-09-04/data/listings.csv.gz"
LOCAL_CSV = "listings.csv.gz"

def load_data():
    if not os.path.exists(LOCAL_CSV):
        print("Downloading dataset from Inside Airbnb...")
        urllib.request.urlretrieve(DATA_URL, LOCAL_CSV)
    df = pd.read_csv(LOCAL_CSV, low_memory=False)

    KEEP = ['id','host_id','neighbourhood_group','neighbourhood',
            'latitude','longitude','room_type','price','minimum_nights',
            'number_of_reviews','last_review','reviews_per_month',
            'calculated_host_listings_count','availability_365']
    df = df[[c for c in KEEP if c in df.columns]].copy()

    # Clean price
    if df['price'].dtype == object:
        df['price'] = df['price'].str.replace('[$,]', '', regex=True).astype(float)
    df = df[df['price'].notna() & (df['price'] > 0)]
    df['price'] = df['price'].clip(upper=1000)

    # Fill / parse
    df['reviews_per_month'] = df['reviews_per_month'].fillna(0)
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')
    df['year_month']  = df['last_review'].dt.to_period('M').astype(str)

    # Standardise boroughs
    valid = ['Manhattan','Brooklyn','Queens','Bronx','Staten Island']
    df = df[df['neighbourhood_group'].isin(valid)].drop_duplicates('id')
    return df

print("Loading data…")
df = load_data()
print(f"Dataset ready: {len(df):,} listings")

# ── Constants ──────────────────────────────────────────────────────────────────
BOROUGHS     = sorted(df['neighbourhood_group'].unique())
ROOM_TYPES   = sorted(df['room_type'].unique())
PRICE_MIN    = int(df['price'].min())
PRICE_MAX    = int(df['price'].quantile(0.99))

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

# ── App layout ─────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    title="NYC Airbnb Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
server = app.server  # expose for Gunicorn / Render

# Shared card style
CARD = {
    'backgroundColor': '#ffffff',
    'border': '1px solid #e8ecf0',
    'borderRadius': '10px',
    'padding': '18px 20px',
    'marginBottom': '16px',
}
KPI_CARD = {
    **CARD,
    'textAlign': 'center',
    'padding': '16px 12px',
    'marginBottom': '0',
}

def kpi(label, id_val):
    return html.Div([
        html.Div(id=id_val, style={
            'fontSize': '26px', 'fontWeight': '700',
            'color': '#1F5F8A', 'lineHeight': '1.1'
        }),
        html.Div(label, style={
            'fontSize': '11px', 'color': '#888',
            'marginTop': '4px', 'textTransform': 'uppercase',
            'letterSpacing': '0.06em'
        }),
    ], style=KPI_CARD)

app.layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.H1("NYC Airbnb Dashboard", style={
                'margin': '0', 'fontSize': '22px', 'fontWeight': '700',
                'color': '#1F5F8A', 'letterSpacing': '-0.02em'
            }),
            html.Div("Capstone Project · Data Analysis with AI · Source: Inside Airbnb",
                     style={'fontSize': '12px', 'color': '#999', 'marginTop': '3px'}),
        ]),
        html.Div("48,895 listings · NYC · 2024", style={
            'fontSize': '12px', 'color': '#aaa',
            'alignSelf': 'center'
        })
    ], style={
        'display': 'flex', 'justifyContent': 'space-between',
        'alignItems': 'flex-start',
        'backgroundColor': '#fff', 'borderBottom': '1px solid #eee',
        'padding': '16px 24px', 'marginBottom': '0'
    }),

    # ── Main body ─────────────────────────────────────────────────────────────
    html.Div([

        # Left sidebar — filters
        html.Div([
            html.Div([
                html.Div("FILTERS", style={
                    'fontSize': '10px', 'fontWeight': '700', 'color': '#aaa',
                    'letterSpacing': '0.1em', 'marginBottom': '14px'
                }),

                html.Label("Borough", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(
                    id='filter-borough',
                    options=[{'label': b, 'value': b} for b in BOROUGHS],
                    multi=True, placeholder="All boroughs",
                    style={'fontSize':'13px','marginBottom':'16px','marginTop':'4px'}
                ),

                html.Label("Room type", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(
                    id='filter-room',
                    options=[{'label': r, 'value': r} for r in ROOM_TYPES],
                    multi=True, placeholder="All room types",
                    style={'fontSize':'13px','marginBottom':'16px','marginTop':'4px'}
                ),

                html.Label("Price range ($/night)", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.RangeSlider(
                    id='filter-price',
                    min=PRICE_MIN, max=PRICE_MAX, step=10,
                    value=[PRICE_MIN, PRICE_MAX],
                    marks={PRICE_MIN: f'${PRICE_MIN}', 200: '$200',
                           500: '$500', PRICE_MAX: f'${PRICE_MAX}+'},
                    tooltip={'placement':'bottom','always_visible':False}
                ),
                html.Div(style={'marginBottom':'16px'}),

                html.Label("Availability", style={'fontSize':'12px','fontWeight':'600','color':'#444'}),
                dcc.Dropdown(
                    id='filter-avail',
                    options=[
                        {'label': 'Any availability', 'value': 'any'},
                        {'label': 'High (180+ days)', 'value': 'high'},
                        {'label': 'Low (< 60 days)',  'value': 'low'},
                    ],
                    value='any', clearable=False,
                    style={'fontSize':'13px','marginBottom':'16px','marginTop':'4px'}
                ),

                html.Hr(style={'borderColor':'#f0f0f0','margin':'8px 0 16px'}),
                html.Div(id='filter-count', style={
                    'fontSize': '12px', 'color': '#888', 'textAlign': 'center'
                }),
            ], style={**CARD, 'marginBottom':'0'}),
        ], style={'width': '220px', 'flexShrink': '0'}),

        # Right main panel
        html.Div([

            # KPI row
            html.Div([
                kpi("Total listings",          'kpi-count'),
                kpi("Median price / night",    'kpi-price'),
                kpi("Avg availability",        'kpi-avail'),
                kpi("Avg reviews / month",     'kpi-reviews'),
                kpi("Multi-listing hosts",     'kpi-multi'),
            ], style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(5, 1fr)',
                'gap': '12px',
                'marginBottom': '16px'
            }),

            # Row 1: Map + Bar chart
            html.Div([
                html.Div([
                    html.Div("Listing map — price & location", style={
                        'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'8px'
                    }),
                    dcc.Graph(id='chart-map', style={'height':'340px'},
                              config={'displayModeBar': False}),
                ], style={**CARD, 'flex':'1.6', 'marginBottom':'0'}),

                html.Div([
                    html.Div("Median price by borough", style={
                        'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'8px'
                    }),
                    dcc.Graph(id='chart-borough-price', style={'height':'340px'},
                              config={'displayModeBar': False}),
                ], style={**CARD, 'flex':'1', 'marginBottom':'0'}),
            ], style={'display':'flex','gap':'14px','marginBottom':'16px'}),

            # Row 2: Time series + Room type donut
            html.Div([
                html.Div([
                    html.Div("Review activity over time (demand proxy)", style={
                        'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'8px'
                    }),
                    dcc.Graph(id='chart-timeseries', style={'height':'280px'},
                              config={'displayModeBar': False}),
                ], style={**CARD, 'flex':'2', 'marginBottom':'0'}),

                html.Div([
                    html.Div("Room type share", style={
                        'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'8px'
                    }),
                    dcc.Graph(id='chart-room-donut', style={'height':'280px'},
                              config={'displayModeBar': False}),
                ], style={**CARD, 'flex':'1', 'marginBottom':'0'}),
            ], style={'display':'flex','gap':'14px','marginBottom':'16px'}),

            # Row 3: Price distribution histogram
            html.Div([
                html.Div("Price distribution of filtered listings", style={
                    'fontSize':'12px','fontWeight':'600','color':'#555','marginBottom':'8px'
                }),
                dcc.Graph(id='chart-price-hist', style={'height':'220px'},
                          config={'displayModeBar': False}),
            ], style={**CARD, 'marginBottom':'0'}),

        ], style={'flex':'1', 'minWidth':'0'}),

    ], style={
        'display': 'flex', 'gap': '16px',
        'padding': '16px 24px',
        'backgroundColor': '#f7f8fa',
        'minHeight': 'calc(100vh - 60px)',
        'fontFamily': '"Helvetica Neue", Helvetica, Arial, sans-serif',
        'boxSizing': 'border-box',
    }),

], style={'backgroundColor':'#f7f8fa', 'minHeight':'100vh'})


# ── Callback ───────────────────────────────────────────────────────────────────
@callback(
    Output('kpi-count',          'children'),
    Output('kpi-price',          'children'),
    Output('kpi-avail',          'children'),
    Output('kpi-reviews',        'children'),
    Output('kpi-multi',          'children'),
    Output('filter-count',       'children'),
    Output('chart-map',          'figure'),
    Output('chart-borough-price','figure'),
    Output('chart-timeseries',   'figure'),
    Output('chart-room-donut',   'figure'),
    Output('chart-price-hist',   'figure'),
    Input('filter-borough', 'value'),
    Input('filter-room',    'value'),
    Input('filter-price',   'value'),
    Input('filter-avail',   'value'),
)
def update_all(boroughs, rooms, price_range, avail):
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

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpi_count   = f"{n:,}"
    kpi_price   = f"${dff['price'].median():.0f}" if n else "—"
    kpi_avail   = f"{dff['availability_365'].mean():.0f}d" if n else "—"
    kpi_reviews = f"{dff['reviews_per_month'].mean():.2f}" if n else "—"
    kpi_multi   = f"{(dff['calculated_host_listings_count'] > 1).mean()*100:.1f}%" if n else "—"
    filter_label = f"{n:,} listings match"

    EMPTY_FIG = go.Figure().update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(text="No data for current filters",
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(color="#aaa", size=13))]
    )

    if n == 0:
        return (kpi_count, kpi_price, kpi_avail, kpi_reviews, kpi_multi,
                filter_label, EMPTY_FIG, EMPTY_FIG, EMPTY_FIG, EMPTY_FIG, EMPTY_FIG)

    BASE_LAYOUT = dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=8, r=8, t=8, b=8),
        font=dict(family='Helvetica Neue, Arial, sans-serif', size=11, color='#444'),
    )

    # ── Map ───────────────────────────────────────────────────────────────────
    map_sample = dff.sample(min(12000, n), random_state=42)
    fig_map = px.scatter_mapbox(
        map_sample,
        lat='latitude', lon='longitude',
        color='neighbourhood_group',
        color_discrete_map=BOROUGH_CLR,
        size='price', size_max=9,
        opacity=0.55,
        hover_data={'price': True, 'room_type': True,
                    'neighbourhood': True, 'latitude': False, 'longitude': False},
        labels={'price': 'Price ($)', 'neighbourhood_group': 'Borough'},
        mapbox_style='carto-positron',
        zoom=10,
        center={'lat': 40.72, 'lon': -73.98}
    )
    fig_map.update_layout(
        **BASE_LAYOUT,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation='h', y=-0.02, x=0,
                    font=dict(size=10), title_text=''),
        showlegend=True,
    )

    # ── Borough bar ───────────────────────────────────────────────────────────
    bdata = (dff.groupby('neighbourhood_group')['price']
               .median().sort_values().reset_index())
    bdata.columns = ['borough', 'median_price']
    fig_bar = go.Figure(go.Bar(
        y=bdata['borough'],
        x=bdata['median_price'],
        orientation='h',
        marker_color=[BOROUGH_CLR.get(b, '#888') for b in bdata['borough']],
        text=[f"${v:.0f}" for v in bdata['median_price']],
        textposition='outside',
        textfont=dict(size=11, color='#444'),
    ))
    fig_bar.update_layout(
        **BASE_LAYOUT,
        xaxis=dict(title='Median price ($)', showgrid=True,
                   gridcolor='#f0f0f0', zeroline=False,
                   tickprefix='$'),
        yaxis=dict(showgrid=False),
        bargap=0.35,
    )

    # ── Time series ───────────────────────────────────────────────────────────
    ts = dff[dff['last_review'].notna()].copy()
    ts['ym'] = ts['last_review'].dt.to_period('M').dt.to_timestamp()
    monthly = ts.groupby('ym').size().reset_index(name='count')
    monthly = monthly[monthly['ym'] >= '2015-01-01']

    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=monthly['ym'], y=monthly['count'],
        mode='lines',
        line=dict(color='#1F5F8A', width=2),
        fill='tozeroy',
        fillcolor='rgba(31,95,138,0.08)',
        name='All boroughs',
    ))
    # COVID band
    fig_ts.add_vrect(x0='2020-03-01', x1='2021-06-01',
                     fillcolor='rgba(186,117,23,0.10)',
                     annotation_text='COVID', annotation_position='top left',
                     annotation_font_size=10, annotation_font_color='#BA7517',
                     line_width=0)
    fig_ts.update_layout(
        **BASE_LAYOUT,
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False,
                   title='Monthly reviews'),
        showlegend=False,
    )

    # ── Room type donut ───────────────────────────────────────────────────────
    room_counts = dff['room_type'].value_counts().reset_index()
    room_counts.columns = ['room_type', 'count']
    fig_donut = go.Figure(go.Pie(
        labels=room_counts['room_type'],
        values=room_counts['count'],
        hole=0.52,
        marker_colors=[ROOM_CLR.get(r, '#888') for r in room_counts['room_type']],
        textinfo='percent',
        textfont_size=11,
        hovertemplate='<b>%{label}</b><br>%{value:,} listings<br>%{percent}<extra></extra>',
    ))
    fig_donut.update_layout(
        **BASE_LAYOUT,
        showlegend=True,
        legend=dict(orientation='v', x=1.01, y=0.5,
                    font=dict(size=10), title_text=''),
        margin=dict(l=0, r=100, t=0, b=0),
    )

    # ── Price histogram ───────────────────────────────────────────────────────
    fig_hist = go.Figure(go.Histogram(
        x=dff['price'],
        nbinsx=60,
        marker_color='#1F5F8A',
        marker_line_color='white',
        marker_line_width=0.4,
        opacity=0.85,
    ))
    median_p = dff['price'].median()
    fig_hist.add_vline(x=median_p, line_dash='dash',
                       line_color='#BA7517', line_width=1.8,
                       annotation_text=f'Median ${median_p:.0f}',
                       annotation_position='top right',
                       annotation_font_size=11,
                       annotation_font_color='#BA7517')
    fig_hist.update_layout(
        **BASE_LAYOUT,
        xaxis=dict(title='Price per night ($)', tickprefix='$',
                   showgrid=False, zeroline=False),
        yaxis=dict(title='Listings', showgrid=True, gridcolor='#f0f0f0', zeroline=False),
        bargap=0.04,
    )

    return (kpi_count, kpi_price, kpi_avail, kpi_reviews, kpi_multi,
            filter_label,
            fig_map, fig_bar, fig_ts, fig_donut, fig_hist)


if __name__ == '__main__':
    app.run(debug=True, port=8050)
