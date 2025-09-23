import pandas as pd
import random
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash.dcc import send_file, send_data_frame
import io

# ------------------------------
# Generate Synthetic Health Data
# ------------------------------
villages = ['Tripura','Assam','Megalaya','Manipur','sikkim']
symptoms_list = ['Diarrhea', 'Fever', 'Vomiting', 'Stomach Pain', 'Hepatitis']

health_records = []
for i in range(1, 51):
    village = random.choice(villages)
    age = random.randint(1, 70)
    symptoms = ','.join(random.sample(symptoms_list, k=random.randint(1, 2)))
    date = (datetime.today() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
    health_records.append([i, age, symptoms, village, date])

health_df = pd.DataFrame(health_records, columns=['Patient_ID','Age','Symptoms','Location','Date'])
health_df['Date'] = pd.to_datetime(health_df['Date'])

# ------------------------------
# Generate Synthetic Water Quality Data
# ------------------------------
water_records = []
for village in villages:
    water_records.append([
        village,
        round(random.uniform(5.0, 9.0), 2),
        round(random.uniform(0, 100), 2),
        random.randint(50, 600)
    ])
water_df = pd.DataFrame(water_records, columns=['Location','pH','Turbidity','Bacterial_Count'])

# Merge Health and Water Data
data = pd.merge(health_df, water_df, on='Location')
data['Risk'] = data.apply(lambda x: 1 if 'Diarrhea' in x['Symptoms'] or x['Bacterial_Count'] > 300 else 0, axis=1)

# ------------------------------
# Initialize Dash App
# ------------------------------
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Health & Water Quality Dashboard", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Select Village:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='village_filter',
            options=[{'label': v, 'value': v} for v in ['All'] + villages],
            value='All', clearable=False
        ),
        html.Br(),
        html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
        dcc.DatePickerRange(
            id='date_filter',
            start_date=data['Date'].min(),
            end_date=data['Date'].max(),
            display_format='YYYY-MM-DD'
        ),
        html.Br(), html.Br(),
        html.Button("Download Filtered Raw Data", id="btn_download_raw", n_clicks=0, style={'marginRight':'10px'}),
        html.Button("Download Summary Data", id="btn_download_summary", n_clicks=0),
        dcc.Download(id="download_raw"),
        dcc.Download(id="download_summary"),
    ], style={'width':'70%', 'margin':'auto'}),
    
    html.Br(),
    dcc.Tabs(id="tabs", value='tab1', children=[
        dcc.Tab(label='Symptoms Distribution', value='tab1'),
        dcc.Tab(label='High-Risk Cases', value='tab2'),
        dcc.Tab(label='Bacterial Count vs Age', value='tab3'),
        dcc.Tab(label='Village Summary Table', value='tab4'),
    ]),
    html.Div(id='tabs-content'),
    html.Div([
        html.Button("Download Graph (PNG)", id="btn_png", n_clicks=0, style={'marginRight':'10px'}),
        html.Button("Download Graph (HTML)", id="btn_html", n_clicks=0)
    ]),
    dcc.Download(id="download_graph")
])

# ------------------------------
# Helper: Filter Data
# ------------------------------
def filter_data(selected_village, start_date, end_date):
    df = data.copy()
    if selected_village != 'All':
        df = df[df['Location']==selected_village]
    df = df[(df['Date']>=pd.to_datetime(start_date)) & (df['Date']<=pd.to_datetime(end_date))]
    return df

# ------------------------------
# Update Tabs Callback
# ------------------------------
@app.callback(
    Output('tabs-content','children'),
    Input('tabs','value'),
    Input('village_filter','value'),
    Input('date_filter','start_date'),
    Input('date_filter','end_date')
)
def update_tab(tab, selected_village, start_date, end_date):
    df = filter_data(selected_village, start_date, end_date)
    if df.empty:
        return html.H3("No data available for this filter.", style={'textAlign':'center','color':'red'})
    
    if tab=='tab1':
        all_symptoms = df['Symptoms'].dropna().str.split(',').sum()
        symptom_counts = pd.Series(all_symptoms).value_counts()
        fig = px.pie(names=symptom_counts.index, values=symptom_counts.values,
                     title=f'Symptom Distribution ({selected_village})')
        return dcc.Graph(id="graph", figure=fig)
    
    elif tab=='tab2':
        risk_count = df.groupby('Location')['Risk'].sum().reset_index()
        fig = px.bar(risk_count, x='Location', y='Risk', color='Risk', text='Risk',
                     title=f'High-Risk Cases ({selected_village})')
        return dcc.Graph(id="graph", figure=fig)
    
    elif tab=='tab3':
        fig = px.scatter(df, x='Bacterial_Count', y='Age', color='Risk', size='Risk',
                         hover_data=['Location','Symptoms'], title=f'Bacterial Count vs Age ({selected_village})')
        return dcc.Graph(id="graph", figure=fig)
    
    elif tab=='tab4':
        summary = df.groupby('Location').agg(
            Total_Cases=('Patient_ID','count'),
            High_Risk_Cases=('Risk','sum'),
            Avg_Bacterial_Count=('Bacterial_Count','mean'),
            Avg_pH=('pH','mean')
        ).reset_index()
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(summary.columns), fill_color='paleturquoise', align='left'),
            cells=dict(values=[summary[c] for c in summary.columns], fill_color='lavender', align='left')
        )])
        return dcc.Graph(id="graph", figure=fig)

# ------------------------------
# CSV Download Callbacks
# ------------------------------
@app.callback(
    Output("download_raw","data"),
    Input("btn_download_raw","n_clicks"),
    Input('village_filter','value'),
    Input('date_filter','start_date'),
    Input('date_filter','end_date'),
    prevent_initial_call=True
)
def download_raw(n_clicks, selected_village, start_date, end_date):
    df = filter_data(selected_village, start_date, end_date)
    return send_data_frame(df.to_csv, filename="filtered_raw_data.csv", index=False)

@app.callback(
    Output("download_summary","data"),
    Input("btn_download_summary","n_clicks"),
    Input('village_filter','value'),
    Input('date_filter','start_date'),
    Input('date_filter','end_date'),
    prevent_initial_call=True
)
def download_summary(n_clicks, selected_village, start_date, end_date):
    df = filter_data(selected_village, start_date, end_date)
    summary = df.groupby('Location').agg(
        Total_Cases=('Patient_ID','count'),
        High_Risk_Cases=('Risk','sum'),
        Avg_Bacterial_Count=('Bacterial_Count','mean'),
        Avg_pH=('pH','mean')
    ).reset_index()
    return send_data_frame(summary.to_csv, filename="summary_data.csv", index=False)

# ------------------------------
# Graph Download Callback
# ------------------------------
@app.callback(
    Output("download_graph","data"),
    Input("btn_png","n_clicks"),
    Input("btn_html","n_clicks"),
    Input('tabs','value'),
    Input('village_filter','value'),
    Input('date_filter','start_date'),
    Input('date_filter','end_date'),
    prevent_initial_call=True
)
def download_graph(btn_png, btn_html, tab, selected_village, start_date, end_date):
    df = filter_data(selected_village, start_date, end_date)

    if tab=='tab1':
        all_symptoms = df['Symptoms'].dropna().str.split(',').sum()
        symptom_counts = pd.Series(all_symptoms).value_counts()
        fig = px.pie(names=symptom_counts.index, values=symptom_counts.values)
        filename="symptoms_chart"
    elif tab=='tab2':
        risk_count = df.groupby('Location')['Risk'].sum().reset_index()
        fig = px.bar(risk_count, x='Location', y='Risk', color='Risk', text='Risk')
        filename="risk_chart"
    elif tab=='tab3':
        fig = px.scatter(df, x='Bacterial_Count', y='Age', color='Risk', size='Risk')
        filename="scatter_chart"
    else:
        summary = df.groupby('Location').agg(
            Total_Cases=('Patient_ID','count'),
            High_Risk_Cases=('Risk','sum'),
            Avg_Bacterial_Count=('Bacterial_Count','mean'),
            Avg_pH=('pH','mean')
        ).reset_index()
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(summary.columns)),
            cells=dict(values=[summary[c] for c in summary.columns])
        )])
        filename="summary_table"

    if btn_png>0:
        buffer = io.BytesIO()
        fig.write_image(buffer, format="png")
        buffer.seek(0)
        return send_file(buffer, filename=f"{filename}.png")

    if btn_html>0:
        buffer = io.StringIO()
        fig.write_html(buffer)
        buffer.seek(0)
        return dict(content=buffer.getvalue(), filename=f"{filename}.html")

# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
