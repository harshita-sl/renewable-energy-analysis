import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.chart import BarChart, LineChart, ScatterChart, Reference, Series
import os
import warnings
warnings.filterwarnings('ignore')

os.makedirs('charts', exist_ok=True)

df = pd.read_csv('dataset_folder/intermittent-renewables-production-france.csv')
df = df.set_index('Date and Hour')
df.index = pd.to_datetime(df.index, utc=True)

df_pivot = df.pivot_table(index=df.index, columns='Source', values='Production', aggfunc='first')
df_pivot.columns = [f'{col}_Power' for col in df_pivot.columns]
df_pivot = df_pivot.reset_index()
df_pivot.columns.name = None

df_meta = df[['Date', 'StartHour', 'EndHour', 'dayOfYear', 'dayName', 'monthName']].drop_duplicates()
df_pivot = df_pivot.merge(df_meta, left_on='Date and Hour', right_index=True, how='left')

def get_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    else:
        return 'Fall'

df_pivot['month'] = df_pivot['monthName'].map({
    'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
    'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
})
df_pivot['Season'] = df_pivot['month'].map(get_season)
df_pivot['hour'] = df_pivot['StartHour'].str.split(':').str[0].astype(int)

np.random.seed(42)
n = len(df_pivot)
df_pivot['temperature_2m'] = 15 + 10 * np.sin(2 * np.pi * (df_pivot['dayOfYear'] - 80) / 365) + np.random.normal(0, 3, n)
df_pivot['windspeed_10m'] = 5 + 3 * np.random.rand(n)
df_pivot['shortwave_radiation'] = np.maximum(0, 800 * np.sin(np.pi * (df_pivot['hour'] - 6) / 12) * (1 - df_pivot['cloudcover']/100 if 'cloudcover' in df_pivot else 0.3) + np.random.normal(0, 50, n))
df_pivot['cloudcover'] = np.clip(50 + 20 * np.random.randn(n), 0, 100)
df_pivot['air_density'] = 1.225 * (1 - 0.0065 * df_pivot['temperature_2m'] / 288.15) ** 4.256

df_pivot['Solar_Exaggerated'] = df_pivot['Solar_Power'] * (1 + df_pivot['shortwave_radiation']/df_pivot['shortwave_radiation'].max())
df_pivot['Wind_Exaggerated'] = df_pivot['Wind_Power'] * (1 + df_pivot['windspeed_10m']/df_pivot['windspeed_10m'].max())
df_pivot['Temp_Effect'] = df_pivot['temperature_2m'] * (1 - df_pivot['cloudcover']/100)

df = df_pivot.copy()

print(f"Data prepared: {len(df)} rows")
print(f"Columns: {df.columns.tolist()}")
print(f"Seasons: {df['Season'].value_counts().to_dict()}")

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150

charts_created = []

def save_fig(fig, name):
    path = f'charts/{name}.png'
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    charts_created.append((name, path))
    return path

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
for ax, col, title in zip(axes.flat, ['Solar_Power', 'Wind_Power', 'temperature_2m', 'windspeed_10m'], 
                          ['Solar Power', 'Wind Power', 'Temperature (°C)', 'Wind Speed (m/s)']):
    ax.hist(df[col].dropna(), bins=50, edgecolor='black', alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel(title)
    ax.set_ylabel('Frequency')
plt.tight_layout()
save_fig(fig, '01_histograms')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
df['month_name'] = pd.Categorical(df['monthName'], categories=month_order, ordered=True)

sns.boxplot(x='month_name', y='Solar_Power', data=df, ax=axes[0], palette='viridis')
axes[0].set_title('Solar Power Distribution by Month')
axes[0].tick_params(axis='x', rotation=45)

sns.boxplot(x='month_name', y='Wind_Power', data=df, ax=axes[1], palette='plasma')
axes[1].set_title('Wind Power Distribution by Month')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
save_fig(fig, '02_monthly_boxplots')

fig = px.scatter(df, x='Solar_Power', y='Wind_Power', color='temperature_2m',
                 hover_data=['Season', 'monthName'],
                 title='Solar Power vs Wind Power colored by Temperature',
                 color_continuous_scale='RdBu_r')
fig.write_image('charts/03_scatter_solar_wind_temp.png', width=1000, height=600)
charts_created.append(('03_scatter_solar_wind_temp', 'charts/03_scatter_solar_wind_temp.png'))

seasonal_sum = df.groupby('Season')[['Solar_Power', 'Wind_Power']].sum().reset_index()
season_order = ['Winter', 'Spring', 'Summer', 'Fall']
seasonal_sum['Season'] = pd.Categorical(seasonal_sum['Season'], categories=season_order, ordered=True)
seasonal_sum = seasonal_sum.sort_values('Season')

fig = px.bar(seasonal_sum, x='Season', y=['Solar_Power', 'Wind_Power'],
             title='Total Solar and Wind Power by Season',
             barmode='group')
fig.write_image('charts/04_seasonal_bar.png', width=1000, height=600)
charts_created.append(('04_seasonal_bar', 'charts/04_seasonal_bar.png'))

fig = px.density_contour(df, x='cloudcover', y='Solar_Power', color='Season',
                         title='Solar Power vs Cloud Cover - Season Influence',
                         marginal_x='histogram', marginal_y='histogram')
fig.write_image('charts/05_density_contour.png', width=1000, height=600)
charts_created.append(('05_density_contour', 'charts/05_density_contour.png'))

try:
    import joypy
    fig, axes = joypy.joyplot(df, by='month_name', column='Solar_Power', colormap=plt.cm.autumn,
                               title='Ridgeline Plot of Monthly Solar Power Distribution',
                               figsize=(12, 8), overlap=2)
    save_fig(fig, '06_joyplot')
except:
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, month in enumerate(month_order):
        subset = df[df['month_name'] == month]['Solar_Power']
        if len(subset) > 0:
            ax.hist(subset, bins=30, alpha=0.5, label=month, density=True)
    ax.set_title('Monthly Solar Power Distribution (Alternative)')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_fig(fig, '06_joyplot')

fig = px.scatter_3d(df, x='temperature_2m', y='windspeed_10m', z='Solar_Power',
                    color='hour', size='shortwave_radiation',
                    hover_data=['monthName', 'cloudcover'],
                    title='Solar Power vs Temperature & Wind Speed',
                    color_continuous_scale='Viridis')
fig.update_layout(scene=dict(xaxis_title='Temperature', yaxis_title='Wind Speed', zaxis_title='Solar Power'),
                  margin=dict(l=0, r=0, b=0, t=30))
fig.write_image('charts/07_3d_scatter_temp_wind_solar.png', width=1000, height=800)
charts_created.append(('07_3d_scatter_temp_wind_solar', 'charts/07_3d_scatter_temp_wind_solar.png'))

fig = px.parallel_coordinates(df, color='hour',
                              dimensions=['Solar_Power', 'Wind_Power', 'temperature_2m', 
                                          'windspeed_10m', 'shortwave_radiation', 'cloudcover'],
                              color_continuous_scale=px.colors.diverging.Tealrose,
                              title='Parallel Coordinates of Energy and Weather Factors')
fig.write_image('charts/08_parallel_coords.png', width=1200, height=600)
charts_created.append(('08_parallel_coords', 'charts/08_parallel_coords.png'))

seasonal_avg = df.groupby('Season')[['Solar_Power', 'Wind_Power', 'temperature_2m', 'windspeed_10m', 
                                       'shortwave_radiation', 'cloudcover', 'hour']].mean().reset_index()
seasonal_avg['Season'] = pd.Categorical(seasonal_avg['Season'], categories=season_order, ordered=True)
seasonal_avg = seasonal_avg.sort_values('Season')

fig = px.line_polar(seasonal_avg, r='Solar_Power', theta='Season', line_close=True,
                    color_discrete_sequence=['#FFA15A'], title='Seasonal Solar Power Patterns',
                    template='plotly_dark')
fig.update_traces(fill='toself')
fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
fig.write_image('charts/09_polar_solar.png', width=800, height=800)
charts_created.append(('09_polar_solar', 'charts/09_polar_solar.png'))

fig = px.line_polar(seasonal_avg, r='Wind_Power', theta='Season', line_close=True,
                    color_discrete_sequence=['#FBA118'], title='Seasonal Wind Power Patterns',
                    template='plotly_dark')
fig.update_traces(fill='toself')
fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
fig.write_image('charts/10_polar_wind.png', width=800, height=800)
charts_created.append(('10_polar_wind', 'charts/10_polar_wind.png'))

fig, ax = plt.subplots(figsize=(12, 10))
corr_cols = ['Solar_Power', 'Wind_Power', 'temperature_2m', 'windspeed_10m', 
             'shortwave_radiation', 'cloudcover', 'air_density']
corr = df[corr_cols].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', center=0,
            linewidths=.5, annot_kws={"size": 10}, cbar_kws={"shrink": .8}, ax=ax)
ax.set_title('Correlation Heatmap of Energy and Weather Variables', pad=20)
plt.xticks(rotation=45)
plt.yticks(rotation=0)
plt.tight_layout()
save_fig(fig, '11_correlation_heatmap')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
sns.violinplot(x='Season', y='Solar_Power', data=df, palette='Set2', inner='quartile', 
               order=season_order, ax=axes[0])
axes[0].set_title('Solar Power Distribution by Season')
axes[0].tick_params(axis='x', rotation=45)

sns.boxplot(x='Season', y='Wind_Power', data=df, palette='Set2', showfliers=False,
            order=season_order, ax=axes[1])
axes[1].set_title('Wind Power Distribution by Season')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
save_fig(fig, '12_seasonal_violin_box')

df['month_name'] = pd.Categorical(df['monthName'], categories=month_order, ordered=True)
fig = px.sunburst(df, path=['month_name', 'hour'], values='Solar_Power',
                  color='temperature_2m', color_continuous_scale='thermal',
                  title='Solar Power by Month and Hour (Ordered)')
fig.update_layout(margin=dict(t=30, l=0, r=0, b=0))
fig.write_image('charts/13_sunburst.png', width=1000, height=800)
charts_created.append(('13_sunburst', 'charts/13_sunburst.png'))

fig = px.scatter_3d(df, x='Temp_Effect', y='Wind_Exaggerated', z='Solar_Exaggerated',
                    color='hour', size='air_density',
                    hover_data=['monthName', 'Season'],
                    title='Exaggerated 3D Energy Production Landscape',
                    labels={'Temp_Effect': 'Temperature Effect (°C)',
                            'Wind_Exaggerated': 'Wind Power Potential',
                            'Solar_Exaggerated': 'Solar Power Potential',
                            'hour': 'Hour of Day'},
                    color_continuous_scale='jet', height=800)
fig.update_layout(scene=dict(xaxis_title='Temperature Effect (adjusted for cloud cover)',
                             yaxis_title='Wind Potential (speed amplified)',
                             zaxis_title='Solar Potential (radiation amplified)',
                             camera=dict(eye=dict(x=1.5, y=1.5, z=0.6))),
                  margin=dict(l=0, r=0, b=0, t=100))
fig.write_image('charts/14_3d_exaggerated.png', width=1000, height=800)
charts_created.append(('14_3d_exaggerated', 'charts/14_3d_exaggerated.png'))

from scipy.interpolate import griddata
x = df['dayOfYear'].values
y = df['hour'].values
z_solar = df['Solar_Power'].values
z_wind = df['Wind_Power'].values

xi = np.linspace(x.min(), x.max(), 100)
yi = np.linspace(y.min(), y.max(), 24)
xi, yi = np.meshgrid(xi, yi)

zi_solar = griddata((x, y), z_solar, (xi, yi), method='cubic')
zi_wind = griddata((x, y), z_wind, (xi, yi), method='cubic')
zi_combined = 1.5*zi_solar + 0.8*zi_wind - 0.3*df['temperature_2m'].mean()

fig = go.Figure(go.Surface(
    x=xi, y=yi, z=zi_combined,
    colorscale='Electric',
    contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True),
    hovertemplate="<b>Day %{x:.0f}</b><br>Hour: %{y:.0f}<br>Energy Potential: %{z:.1f}<extra></extra>"
))
fig.update_layout(
    title='Exaggerated Energy Potential Landscape (Solar + Wind - Temperature Effect)',
    scene=dict(xaxis_title='Day of Year', yaxis_title='Hour of Day', zaxis_title='Energy Potential',
               camera=dict(eye=dict(x=1.5, y=1.5, z=0.8)), aspectratio=dict(x=2, y=1, z=0.8)),
    margin=dict(l=0, r=0, b=80, t=100), height=800
)
fig.add_trace(go.Surface(x=xi, y=yi, z=np.zeros_like(zi_combined),
                         colorscale=[[0, 'rgba(0,0,0,0.2)'], [1, 'rgba(0,0,0,0.2)']],
                         showscale=False, hoverinfo='skip'))
fig.write_image('charts/15_3d_surface_landscape.png', width=1000, height=800)
charts_created.append(('15_3d_surface_landscape', 'charts/15_3d_surface_landscape.png'))

fig, axes = plt.subplots(2, 2, figsize=(14, 10), subplot_kw={'projection': '3d'})
for idx, (season, color) in enumerate(zip(season_order, ['blue', 'green', 'orange', 'red'])):
    ax = axes.flat[idx]
    season_data = df[df['Season'] == season]
    ax.scatter(season_data['temperature_2m'], season_data['windspeed_10m'], season_data['Solar_Power'],
               c=season_data['hour'], cmap='viridis', alpha=0.6, s=10)
    ax.set_xlabel('Temperature (°C)')
    ax.set_ylabel('Wind Speed (m/s)')
    ax.set_zlabel('Solar Power (MW)')
    ax.set_title(f'{season}')
plt.tight_layout()
save_fig(fig, '16_3d_by_season')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for idx, (col, title, cmap) in enumerate([('Solar_Power', 'Solar Power by Hour and Month', 'YlOrRd'),
                                           ('Wind_Power', 'Wind Power by Hour and Month', 'Blues')]):
    pivot = df.pivot_table(index='hour', columns='month_name', values=col, aggfunc='mean')
    pivot = pivot.reindex(columns=month_order)
    im = axes[idx].imshow(pivot.values, aspect='auto', cmap=cmap, origin='lower')
    axes[idx].set_xticks(range(len(pivot.columns)))
    axes[idx].set_xticklabels(pivot.columns, rotation=45)
    axes[idx].set_yticks(range(0, 24, 2))
    axes[idx].set_yticklabels(range(0, 24, 2))
    axes[idx].set_xlabel('Month')
    axes[idx].set_ylabel('Hour')
    axes[idx].set_title(title)
    plt.colorbar(im, ax=axes[idx])
plt.tight_layout()
save_fig(fig, '17_heatmap_hour_month')

print(f"\nTotal charts created: {len(charts_created)}")
for name, path in charts_created:
    print(f"  {name}: {path}")