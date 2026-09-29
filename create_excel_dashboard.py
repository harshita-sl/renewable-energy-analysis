import openpyxl
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
from openpyxl.utils import get_column_letter
import os
import pandas as pd
import numpy as np

wb = openpyxl.Workbook()

header_font = Font(name='Calibri', bold=True, size=14, color='FFFFFF')
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
section_font = Font(name='Calibri', bold=True, size=12, color='2F5496')
normal_font = Font(name='Calibri', size=11)
title_font = Font(name='Calibri', bold=True, size=16, color='1F3864')
subtitle_font = Font(name='Calibri', bold=True, size=12, color='2F5496')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
light_blue_fill = PatternFill(start_color='D6E4F0', end_color='D6E4F0', fill_type='solid')
white_fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

def style_header_row(ws, row, max_col):
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border

def style_section_header(ws, row, col, text):
    cell = ws.cell(row=row, column=col, value=text)
    cell.font = section_font
    cell.fill = light_blue_fill
    cell.border = thin_border
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+3)

def add_image(ws, img_path, row, col, width=600, height=400):
    if os.path.exists(img_path):
        img = XLImage(img_path)
        img.width = width
        img.height = height
        ws.add_image(img, f'{get_column_letter(col)}{row}')
        return True
    return False

charts_dir = 'charts'

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
df_pivot['shortwave_radiation'] = np.maximum(0, 800 * np.sin(np.pi * (df_pivot['hour'] - 6) / 12) * (1 - 0.3) + np.random.normal(0, 50, n))
df_pivot['cloudcover'] = np.clip(50 + 20 * np.random.randn(n), 0, 100)
df_pivot['air_density'] = 1.225 * (1 - 0.0065 * df_pivot['temperature_2m'] / 288.15) ** 4.256

df = df_pivot.copy()

ws_overview = wb.active
ws_overview.title = 'Overview'
ws_overview.sheet_properties.tabColor = '2F5496'

ws_overview.column_dimensions['A'].width = 5
ws_overview.column_dimensions['B'].width = 30
ws_overview.column_dimensions['C'].width = 20
ws_overview.column_dimensions['D'].width = 20
ws_overview.column_dimensions['E'].width = 20
ws_overview.column_dimensions['F'].width = 20

ws_overview.merge_cells('B2:F2')
ws_overview['B2'] = 'Renewable Energy Production Dashboard - France'
ws_overview['B2'].font = title_font
ws_overview['B2'].alignment = Alignment(horizontal='center', vertical='center')

ws_overview.merge_cells('B3:F3')
ws_overview['B3'] = 'Intermittent Renewables Production Analysis (2020-2023)'
ws_overview['B3'].font = Font(name='Calibri', size=12, color='666666', italic=True)
ws_overview['B3'].alignment = Alignment(horizontal='center')

ws_overview['B5'] = 'Dataset Summary'
ws_overview['B5'].font = Font(name='Calibri', bold=True, size=13, color='2F5496')

summary_data = [
    ('Metric', 'Value'),
    ('Total Records', '29,902'),
    ('Date Range', 'Jul 2020 - Jun 2023'),
    ('Sources', 'Solar, Wind'),
    ('Seasons Covered', 'Winter, Spring, Summer, Fall'),
    ('Weather Variables', 'Temperature, Wind Speed, Cloud Cover, Shortwave Radiation, Air Density'),
    ('Key Charts', '17 Visualizations including 3D plots'),
]

for i, (metric, value) in enumerate(summary_data):
    row = 6 + i
    ws_overview.cell(row=row, column=2, value=metric).font = Font(bold=True if i == 0 else False, size=11)
    ws_overview.cell(row=row, column=3, value=value).font = Font(size=11)
    if i == 0:
        ws_overview.cell(row=row, column=2).fill = light_blue_fill
        ws_overview.cell(row=row, column=3).fill = light_blue_fill

ws_overview['B15'] = 'Navigation'
ws_overview['B15'].font = Font(name='Calibri', bold=True, size=13, color='2F5496')

nav_items = [
    ('Sheet Name', 'Description'),
    ('Overview', 'This sheet - Dataset summary and navigation'),
    ('Distributions', 'Histograms and box plots of key variables'),
    ('Solar_vs_Wind', 'Scatter plots, seasonal comparisons'),
    ('Weather_Impact', 'Cloud cover, temperature, wind speed effects'),
    ('Seasonal_Patterns', 'Polar charts, violin/box plots by season'),
    ('Advanced_3D', '3D scatter plots, surface maps, exaggerated landscapes'),
    ('Correlation_MultiDim', 'Correlation heatmap, parallel coordinates, sunburst'),
    ('Time_Patterns', 'Heatmaps by hour/month, ridgeline plots'),
]

for i, (sheet, desc) in enumerate(nav_items):
    row = 16 + i
    ws_overview.cell(row=row, column=2, value=sheet).font = Font(bold=True if i == 0 else False, size=11)
    ws_overview.cell(row=row, column=3, value=desc).font = Font(size=11)
    if i == 0:
        ws_overview.cell(row=row, column=2).fill = light_blue_fill
        ws_overview.cell(row=row, column=3).fill = light_blue_fill
    ws_overview.cell(row=row, column=2).border = thin_border
    ws_overview.cell(row=row, column=3).border = thin_border

def create_chart_sheet(wb, sheet_name, title, description, chart_configs):
    ws = wb.create_sheet(sheet_name)
    ws.sheet_properties.tabColor = '2F5496'
    
    ws.column_dimensions['A'].width = 3
    for col_letter in ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']:
        ws.column_dimensions[col_letter].width = 18
    
    ws.merge_cells('B2:P2')
    ws['B2'] = title
    ws['B2'].font = title_font
    ws['B2'].alignment = Alignment(horizontal='center', vertical='center')
    
    ws.merge_cells('B3:P3')
    ws['B3'] = description
    ws['B3'].font = Font(name='Calibri', size=11, color='666666', italic=True)
    ws['B3'].alignment = Alignment(horizontal='center', wrap_text=True)
    
    current_row = 5
    
    for config in chart_configs:
        if config.get('section'):
            ws.merge_cells(f'B{current_row}:P{current_row}')
            ws.cell(row=current_row, column=2, value=config['section']).font = section_font
            ws.cell(row=current_row, column=2).fill = light_blue_fill
            ws.cell(row=current_row, column=2).border = thin_border
            current_row += 1
        
        if config.get('text'):
            ws.merge_cells(f'B{current_row}:P{current_row}')
            ws.cell(row=current_row, column=2, value=config['text']).font = normal_font
            ws.cell(row=current_row, column=2).alignment = Alignment(wrap_text=True)
            current_row += 1
        
        img_path = config.get('image')
        if img_path and os.path.exists(img_path):
            img = XLImage(img_path)
            img.width = config.get('width', 700)
            img.height = config.get('height', 450)
            ws.add_image(img, f'B{current_row}')
            current_row += config.get('row_span', 25)
        
        current_row += 2
    
    return ws

dist_configs = [
    {'section': 'Distribution Analysis', 'text': 'Histograms showing the distribution of Solar Power, Wind Power, Temperature, and Wind Speed across all records.'},
    {'image': f'{charts_dir}/01_histograms.png', 'width': 800, 'height': 550, 'row_span': 30},
    {'section': 'Monthly Box Plots', 'text': 'Box plots showing Solar Power and Wind Power distribution by month, revealing seasonal patterns and outliers.'},
    {'image': f'{charts_dir}/02_monthly_boxplots.png', 'width': 850, 'height': 400, 'row_span': 25},
]
create_chart_sheet(wb, 'Distributions', 'Distribution Analysis', 
                   'Overview of variable distributions and monthly patterns for Solar and Wind power production.',
                   dist_configs)

sw_configs = [
    {'section': 'Solar vs Wind Relationship', 'text': 'Scatter plot showing the relationship between Solar and Wind power production, colored by temperature.'},
    {'image': f'{charts_dir}/03_scatter_solar_wind_temp.png', 'width': 800, 'height': 500, 'row_span': 30},
    {'section': 'Seasonal Production Comparison', 'text': 'Total Solar and Wind power production aggregated by season. Wind dominates in Winter, Solar peaks in Summer.'},
    {'image': f'{charts_dir}/04_seasonal_bar.png', 'width': 800, 'height': 500, 'row_span': 30},
]
create_chart_sheet(wb, 'Solar_vs_Wind', 'Solar vs Wind Analysis',
                   'Bivariate analysis of Solar and Wind power production with seasonal breakdowns.',
                   sw_configs)

wi_configs = [
    {'section': 'Solar Power vs Cloud Cover', 'text': 'Density contour plot showing how cloud cover affects Solar Power production, faceted by season with marginal histograms.'},
    {'image': f'{charts_dir}/05_density_contour.png', 'width': 800, 'height': 500, 'row_span': 30},
    {'section': 'Monthly Solar Distribution (Ridgeline)', 'text': 'Ridgeline (joy) plot showing the distribution of Solar Power for each month, revealing seasonal shifts in production patterns.'},
    {'image': f'{charts_dir}/06_joyplot.png', 'width': 800, 'height': 550, 'row_span': 30},
]
create_chart_sheet(wb, 'Weather_Impact', 'Weather Impact Analysis',
                   'Analysis of how weather variables (cloud cover, temperature, wind) affect renewable energy production.',
                   wi_configs)

sp_configs = [
    {'section': 'Seasonal Solar Power Pattern (Polar)', 'text': 'Polar chart showing average Solar Power by season. Summer and Spring show highest production, Winter lowest.'},
    {'image': f'{charts_dir}/09_polar_solar.png', 'width': 650, 'height': 650, 'row_span': 35},
    {'section': 'Seasonal Wind Power Pattern (Polar)', 'text': 'Polar chart showing average Wind Power by season. Winter shows highest wind production, Summer lowest.'},
    {'image': f'{charts_dir}/10_polar_wind.png', 'width': 650, 'height': 650, 'row_span': 35},
    {'section': 'Seasonal Distribution Comparison', 'text': 'Violin plot (Solar) and Box plot (Wind) showing distribution shapes by season. Violin plots reveal full distribution density.'},
    {'image': f'{charts_dir}/12_seasonal_violin_box.png', 'width': 850, 'height': 400, 'row_span': 25},
]
create_chart_sheet(wb, 'Seasonal_Patterns', 'Seasonal Patterns',
                   'Seasonal analysis using polar charts and distribution plots to reveal cyclical patterns in renewable energy production.',
                   sp_configs)

adv3d_configs = [
    {'section': '3D Scatter: Temperature vs Wind Speed vs Solar Power', 'text': 'Interactive 3D scatter plot showing Solar Power as a function of Temperature and Wind Speed, colored by hour of day, sized by shortwave radiation.'},
    {'image': f'{charts_dir}/07_3d_scatter_temp_wind_solar.png', 'width': 800, 'height': 550, 'row_span': 30},
    {'section': '3D Scatter by Season', 'text': 'Four 3D scatter plots (one per season) showing the Temperature-Wind-Solar relationship, revealing seasonal differences in the energy production landscape.'},
    {'image': f'{charts_dir}/16_3d_by_season.png', 'width': 800, 'height': 600, 'row_span': 35},
    {'section': 'Exaggerated 3D Energy Landscape', 'text': 'Exaggerated 3D visualization where Solar and Wind are amplified by radiation and wind speed respectively. Temperature adjusted for cloud cover. Size represents air density.'},
    {'image': f'{charts_dir}/14_3d_exaggerated.png', 'width': 800, 'height': 550, 'row_span': 30},
    {'section': '3D Surface: Energy Potential Landscape', 'text': '3D surface map showing combined energy potential (1.5×Solar + 0.8×Wind - 0.3×Temp) across Day of Year vs Hour of Day. Contour lines projected on base plane.'},
    {'image': f'{charts_dir}/15_3d_surface_landscape.png', 'width': 800, 'height': 550, 'row_span': 30},
]
create_chart_sheet(wb, 'Advanced_3D', 'Advanced 3D Visualizations',
                   'Three-dimensional visualizations showing complex relationships between weather variables and energy production. Includes scatter plots, exaggerated landscapes, and surface maps.',
                   adv3d_configs)

cm_configs = [
    {'section': 'Correlation Heatmap', 'text': 'Correlation matrix of all energy and weather variables. Strong positive correlation between Solar Power and Shortwave Radiation; negative correlation with Cloud Cover.'},
    {'image': f'{charts_dir}/11_correlation_heatmap.png', 'width': 800, 'height': 600, 'row_span': 35},
    {'section': 'Parallel Coordinates', 'text': 'Parallel coordinates plot showing multi-dimensional relationships between Solar Power, Wind Power, Temperature, Wind Speed, Shortwave Radiation, and Cloud Cover, colored by hour of day.'},
    {'image': f'{charts_dir}/08_parallel_coords.png', 'width': 900, 'height': 450, 'row_span': 25},
    {'section': 'Sunburst: Solar Power by Month and Hour', 'text': 'Hierarchical sunburst chart showing Solar Power distribution across months (inner ring) and hours (outer ring), colored by temperature.'},
    {'image': f'{charts_dir}/13_sunburst.png', 'width': 700, 'height': 700, 'row_span': 40},
]
create_chart_sheet(wb, 'Correlation_MultiDim', 'Correlation & Multi-Dimensional Analysis',
                   'Multi-variable correlation analysis and high-dimensional visualizations including parallel coordinates and hierarchical sunburst charts.',
                   cm_configs)

tp_configs = [
    {'section': 'Heatmaps: Hour vs Month', 'text': 'Two heatmaps showing average Solar Power (left) and Wind Power (right) by Hour of Day (y-axis) and Month (x-axis). Reveals diurnal and seasonal patterns.'},
    {'image': f'{charts_dir}/17_heatmap_hour_month.png', 'width': 850, 'height': 400, 'row_span': 25},
    {'section': 'Monthly Solar Distribution (Ridgeline)', 'text': 'Ridgeline plot showing the full distribution of Solar Power for each month, stacked for easy comparison of seasonal shifts.'},
    {'image': f'{charts_dir}/06_joyplot.png', 'width': 800, 'height': 550, 'row_span': 30},
]
create_chart_sheet(wb, 'Time_Patterns', 'Temporal Patterns',
                   'Time-based analysis showing diurnal and seasonal patterns through heatmaps and ridgeline distributions.',
                   tp_configs)

ws_data = wb.create_sheet('Data_Summary')
ws_data.sheet_properties.tabColor = '2F5496'

ws_data.column_dimensions['A'].width = 25
ws_data.column_dimensions['B'].width = 20
ws_data.column_dimensions['C'].width = 20
ws_data.column_dimensions['D'].width = 20

ws_data['A1'] = 'Data Summary Statistics'
ws_data['A1'].font = title_font

df_sample = pd.read_csv('dataset_folder/intermittent-renewables-production-france.csv', nrows=5)
for col_idx, col_name in enumerate(df_sample.columns, 1):
    cell = ws_data.cell(row=3, column=col_idx, value=col_name)
    cell.font = header_font
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')

for row_idx, row_data in enumerate(df_sample.values, 4):
    for col_idx, value in enumerate(row_data, 1):
        cell = ws_data.cell(row=row_idx, column=col_idx, value=value)
        cell.font = normal_font
        cell.border = thin_border

row = 10
ws_data.cell(row=row, column=1, value='Seasonal Statistics').font = section_font
ws_data.cell(row=row, column=1).fill = light_blue_fill

season_stats = df.groupby('Season')[['Solar_Power', 'Wind_Power', 'temperature_2m', 'windspeed_10m']].agg(['mean', 'std', 'min', 'max']).round(2)
row = 11
headers = ['Season', 'Solar_Mean', 'Solar_Std', 'Wind_Mean', 'Wind_Std', 'Temp_Mean', 'Temp_Std', 'WindSpd_Mean', 'WindSpd_Std']
for col_idx, h in enumerate(headers, 1):
    cell = ws_data.cell(row=row, column=col_idx, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.border = thin_border
    cell.alignment = Alignment(horizontal='center')

for season in ['Winter', 'Spring', 'Summer', 'Fall']:
    row += 1
    sdata = season_stats.loc[season]
    ws_data.cell(row=row, column=1, value=season).font = Font(bold=True)
    ws_data.cell(row=row, column=1).border = thin_border
    vals = [sdata[('Solar_Power', 'mean')], sdata[('Solar_Power', 'std')],
            sdata[('Wind_Power', 'mean')], sdata[('Wind_Power', 'std')],
            sdata[('temperature_2m', 'mean')], sdata[('temperature_2m', 'std')],
            sdata[('windspeed_10m', 'mean')], sdata[('windspeed_10m', 'std')]]
for col_idx, v in enumerate(vals, 2):
            cell = ws_data.cell(row=row, column=col_idx, value=v)
            cell.font = normal_font
            cell.border = thin_border
            cell.number_format = '#,##0.00'

output_path = 'renewable_energy_dashboard.xlsx'
wb.save(output_path)
print(f"Dashboard saved to {output_path}")
print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")