# renewable-energy-analysis

## Overview

This Jupyter notebook performs exploratory data analysis and visualization on France's intermittent renewable energy production data. The analysis examines solar and wind power generation across different seasons, weather conditions, and time patterns, using a dataset of 59,806 hourly records from July 2020 to June 2023.

## Dataset

- **File**: `dataset_folder/intermittent-renewables-production-france.csv`
- **Records**: 59,806 hourly entries
- **Time range**: 2020-07-22 to 2023-06-30
- **Sources**: Solar and Wind power production
- **Key variables**:
  - `Production` (MW): Energy output
  - `temperature_2m` (°C): 2-meter temperature
  - `windspeed_10m` (m/s): 10-meter wind speed
  - `shortwave_radiation`: Solar radiation
  - `cloudcover` (%): Cloud cover percentage
  - `air_density`: Air density
  - `hour`, `month`, `season`: Temporal groupings

## Notebook Structure

The notebook is organized into cells that progressively explore the data:

1. **Data Loading & Preparation**
   - Uploads and extracts the dataset ZIP
   - Loads CSV and sets datetime index
   - Creates `Season` column (Winter/Spring/Summer/Fall based on month)
   - Converts index to UTC datetime

2. **Basic Exploration**
   - Season distribution analysis
   - Duplicate checks
   - Basic descriptive statistics

3. **Weather & Production Relationships**
   - Histograms of Solar Power, Wind Power, and Temperature
   - Boxplot of Solar Power by month
   - Scatter: Solar vs Wind colored by temperature
   - Bar chart: Total Solar & Wind power by Season
   - Ridgeline plot: Monthly Solar Power distribution

4. **Multi-Dimensional Visualizations**
   - 3D scatter: Solar Power vs Temperature & Wind Speed
   - Parallel coordinates: All energy and weather factors
   - Polar charts: Seasonal patterns for Solar and Wind power
   - Sunburst: Solar Power by Month and Hour (ordered)
   - Exaggerated 3D Energy Production Landscape
   - Energy Potential Landscape (3D surface with contours)

5. **Statistical Analysis**
   - Correlation heatmap of all energy/weather variables
   - Violin plots: Solar Power distribution by Season
   - Box plots: Wind Power distribution by Season

## Dependencies

The notebook requires the following Python packages:

- `tensorflow` / `keras`
- `numpy`
- `pandas`
- `matplotlib`
- `seaborn`
- `plotly`
- `joypy` (for ridgeline plots)
- `scipy`

Install with:
```bash
pip install tensorflow keras numpy pandas matplotlib seaborn plotly joypy scipy
```

## Usage

```bash
jupyter notebook renewable_energy.ipynb
```

Or run in Google Colab by uploading the notebook and the dataset ZIP file.

## Key Findings Explored

- Seasonal variations in solar and wind power production
- Impact of temperature, wind speed, and cloud cover on energy output
- Daily and hourly production patterns
- Relationships between multiple weather variables and energy production
- Correlation structure between all analyzed variables

## Output

All visualizations are rendered interactively using Plotly. The notebook generates numerous plots showing:
- Distribution of power output by season and month
- How weather conditions affect solar and wind generation
- Multi-dimensional relationships between energy production and meteorological factors
- Time-based patterns (hour-of-day, day-of-year effects)
