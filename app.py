# -*- coding: utf-8 -*-
"""Visualization_Z_Y.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1yKpqI2-R12v6M4lD9JV5rC2umDtRPPM_

## Pip install
"""

# Install necessary packages


"""## Imports"""

# Import the libraries
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
# from google.colab import output
import pycountry_convert as pc
from dash.dependencies import Input, Output, State
import numpy as np
import logging

"""## Import Datssets"""

# Load data
country_codes = pd.read_csv('country_codes.csv')
all_regions = pd.read_csv('all_regions.csv')

def handle_bad_lines(row):
    print(f"Skipping bad line: {row}")
    return 0  # Skips the bad line

athlete_data = pd.read_csv('all_athlete_games.csv',on_bad_lines='skip', engine='python')

"""## Some pre-processing"""

# Merge datasets on the country code
merged_data = pd.merge(athlete_data, country_codes, left_on='NOC', right_on='country_code', how='left')
merged_data = pd.merge(merged_data, all_regions, left_on='NOC', right_on='NOC', how='left')
# Group by country and medal type, then pivot to get counts for each medal type
# Aggregate data to get total medals per country
medals_per_country = merged_data.groupby(['Region',  'Season', 'Medal'])['Medal'].count().unstack().fillna(0).reset_index()

# Ensure the columns for Gold, Silver, and Bronze are present and convert to integers
if 'Gold' not in medals_per_country.columns:
    medals_per_country['Gold'] = 0
else:
    medals_per_country['Gold'] = medals_per_country['Gold'].astype(int)

if 'Silver' not in medals_per_country.columns:
    medals_per_country['Silver'] = 0
else:
    medals_per_country['Silver'] = medals_per_country['Silver'].astype(int)

if 'Bronze' not in medals_per_country.columns:
    medals_per_country['Bronze'] = 0
else:
    medals_per_country['Bronze'] = medals_per_country['Bronze'].astype(int)

# Calculate the total number of medals
medals_per_country['Total Medals'] = medals_per_country['Gold'] + medals_per_country['Silver'] + medals_per_country['Bronze']

# medals_per_country# Check the resulting DataFrame
# medals_per_country.head()

"""## Interactive map function"""

def create_map(df, selected_season, selected_medals):
    # Filter the DataFrame based on the selected season
    df_filtered = df[df['Season'] == selected_season].copy()

    # Filter for selected medals and calculate the total medals
    df_filtered['Total'] = 0  # Initialize the total column

    if 'Gold' in selected_medals:
        df_filtered['Total'] += df_filtered['Gold']
    if 'Silver' in selected_medals:
        df_filtered['Total'] += df_filtered['Silver']
    if 'Bronze' in selected_medals:
        df_filtered['Total'] += df_filtered['Bronze']

    # Choose the color scale based on the season
    if selected_season == 'Winter':
        color_scale = px.colors.sequential.Blues  # Blue for Winter
    else:
        color_scale = px.colors.sequential.Reds  # Red for Summer

    # Create a choropleth map with the chosen color scale
    fig = px.choropleth(
        df_filtered,
        locations="Region",
        locationmode="country names",
        color="Total",
        hover_name="Region",
        color_continuous_scale=color_scale,
        title=f"Total Olympic Medals by Country ({selected_season} Games)"
    )

    # Update the geos to better define the borders and enable zoom controls
    fig.update_geos(
        showcoastlines=True, coastlinecolor="Black",
        showland=True, landcolor="LightGray",
        showcountries=True, countrycolor="Black",
        showframe=False,
        fitbounds="locations",  # Auto-zoom to fit all locations
        visible=True
    )



    return fig

"""## GDP and Medals visualization function"""

# Load the datasets

gdp_data = pd.read_csv('gdp_data.csv')  # Contains columns: Country, Year, GDP
population_data = pd.read_csv('World-population-by-countries-dataset.csv')  # Contains columns: Country, Year, Population

# Identify columns that represent years by checking if they can be converted to integers
year_columns = population_data.columns[population_data.columns.str.isdigit()]

# Identify non-year columns

non_year_columns = ['Country Name', 'Country Code']  # Remove 'Indicator Name' if it's not present
# Filter out only the year columns for melting
population_data_melted = population_data.melt(id_vars=non_year_columns,
                                              value_vars=year_columns,
                                              var_name='Year',
                                              value_name='Population')

# Convert 'Year' to integer
population_data_melted['Year'] = population_data_melted['Year'].astype(int)
# Ensure Year is already an integer
population_data_melted['Year'] = population_data_melted['Year'].astype(int)

# Convert Population to numeric, forcing errors to NaN, then drop these rows
population_data_melted['Population'] = pd.to_numeric(population_data_melted['Population'], errors='coerce')

# Drop rows where Population is NaN (i.e., non-numeric values were coerced to NaN)
population_data_melted = population_data_melted.dropna(subset=['Population'])

medals_per_country_years = merged_data.groupby(['NOC','Region', 'Year', 'Season', 'Medal'])['Medal'].count().unstack().fillna(0).reset_index()
# Ensure that the medals_per_country_years table only contains data from 1960 onwards
medals_per_country_years = medals_per_country_years[medals_per_country_years['Year'] >= 1960]

# Rename columns in the GDP and Population data to match the medals DataFrame
gdp_data.rename(columns={'country_name': 'Region', 'year': 'Year'}, inplace=True)
medals_per_country_years.rename(columns={'NOC': 'country_code'}, inplace=True)
population_data_melted.rename(columns={'Country Name': 'Region', 'Year': 'Year','Country Code' : 'country_code'}, inplace=True)

# Now merge the medals data with GDP data
combined_data = pd.merge(medals_per_country_years, gdp_data, on=['country_code', 'Year'], how='left')

# Merge the result with population data
combined_data = pd.merge(combined_data, population_data_melted, on=['country_code', 'Year'], how='left')

# Rename 'value' to 'GDP' in the combined_data DataFrame
combined_data.rename(columns={'value': 'GDP'}, inplace=True)

# Calculate 'Total Medals' by summing up Gold, Silver, and Bronze columns
combined_data['Total Medals'] = combined_data['Gold'] + combined_data['Silver'] + combined_data['Bronze']

def country_code_to_continent(country_code):
    try:
        if pd.isna(country_code):
            return 'Unknown'
        # Convert country code to continent code
        continent_code = pc.country_alpha2_to_continent_code(pc.country_alpha3_to_country_alpha2(str(country_code)))
        # Convert continent code to continent name
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except KeyError:
      return 'Unknown'
# Apply the function to your DataFrame
combined_data['Continent'] = combined_data['country_code'].apply(country_code_to_continent)

def create_full_years_data(df):
    # Create a DataFrame with all years from 1960 to 2020
    all_years = pd.DataFrame({'Year': range(1960, 2021, 4)})

    # Get a unique list of all regions (countries)
    all_countries = df[['Region', 'country_code']].drop_duplicates()

    # Cross join countries with years to create a full grid of all possible combinations
    full_data = all_countries.assign(key=1).merge(all_years.assign(key=1), on='key').drop('key', axis=1)

    # Merge this full grid with the original data to ensure every year is represented
    df_full = full_data.merge(df, on=['Region', 'country_code', 'Year'], how='left').sort_values(by=['Region', 'Year'])

    # Forward fill to ensure missing data is filled with the last known values
    df_full = df_full.groupby('Region').apply(lambda group: group.ffill().bfill()).reset_index(drop=True)

    return df_full


def create_animated_scatter_plot(df):
    # Apply cumulative data creation to ensure no country disappears
    df = create_full_years_data(df)

    # Define the range and tick values for the x-axis (Cumulative Medals) in log scale
    range_x_values = [1, df['Cumulative Medals'].max() + 500]
    x_ticks = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]

    # Define the range and tick values for the y-axis (GDP) in log scale
    y_ticks = [1e9, 1e10, 1e11, 1e12, 1e13]  # Example: 1B, 10B, 100B, 1T, 10T
    range_y_values = [df['GDP'].min() * 0.8, df['GDP'].max() * 1.5]

    # Create the animated scatter plot
    fig = px.scatter(
        df,
        x="Cumulative Medals",
        y="GDP",
        size="Population",
        color="Continent",
        hover_name="Region",
        animation_frame="Year",
        animation_group="Region",
        log_x=True,  # Apply log scale to the x-axis
        log_y=True,  # Apply log scale to the y-axis
        size_max=80,  # Slightly decrease size_max to prevent large dots from overflowing
        title="Cumulative Olympic Medals vs GDP over Time (Dot size ~ Population size)",
        labels={"Cumulative Medals": "Log of Cumulative Medals", "GDP": "Log of GDP"},
        range_x=range_x_values,  # Set the defined range for the x-axis
        range_y=range_y_values,  # Set the defined range for the y-axis
        category_orders={"Year": [str(year) for year in range(1960, 2021, 4)]}
    )

    # Update x-axis to show specific tick values with corresponding labels
    fig.update_xaxes(
        tickvals=x_ticks,
        ticktext=[str(val) for val in x_ticks],
        title_text="Cumulative Medals"
    )

    # Update y-axis to show specific tick values with corresponding labels
    fig.update_yaxes(
        tickvals=y_ticks,
        ticktext=["1B", "10B", "100B", "1T", "10T"],  # Use abbreviated labels for readability
        title_text="GDP"
    )

    return fig
combined_data['Population'] = pd.to_numeric(combined_data['Population'], errors='coerce')

# Remove rows where any column has NaN values
combined_data_cleaned = combined_data.dropna()

# Ensure the data is sorted by Region (country) and Year
combined_data_cleaned = combined_data_cleaned.sort_values(by=['Region', 'Year'])

# Calculate cumulative sum for Total Medals by country over the years
combined_data_cleaned['Cumulative Medals'] = combined_data_cleaned.groupby('Region')['Total Medals'].cumsum()

# usa_data1 = combined_data_cleaned[combined_data_cleaned['country_code'] == 'RUS']
# usa_data2 = medals_per_country_years[medals_per_country_years['Region'] == 'USA']
# usa_data3 = gdp_data[gdp_data['country_code'] == 'USA']
# usa_data4 = combined_data[combined_data['country_code'] == 'USA']
# Display the first few rows of the filtered data


# Create a dictionary mapping country names to their codes, ensuring uniqueness
country_name_to_code = {row['Region']: row['country_code'] for index, row in combined_data_cleaned.drop_duplicates(subset=['Region']).iterrows()}

"""## Bar plot function"""

def create_medal_bar_plot(df, selected_sport, selected_season, selected_year):
    # Filter data by the selected season
    df = df[df['Season'] == selected_season]

    # Filter data up to the selected year
    df = df[df['Year'] <= selected_year]

    # Filter data by the selected sport
    df = df[df['Sport'] == selected_sport]

    # Group by country and calculate cumulative medals
    df['Cumulative Medals'] = df.groupby('Team')['Medal'].cumcount() + 1

    medals_by_country = df.groupby('Team')['Cumulative Medals'].max().reset_index()

    # Sort the data from highest to lowest and keep only the top 10 countries
    top_medals_by_country = medals_by_country.nlargest(10, 'Cumulative Medals').sort_values(by='Cumulative Medals', ascending=False)

    # Create the bar plot with the same color for all bars
    fig = px.bar(
        top_medals_by_country,
        x='Team',
        y='Cumulative Medals',
        title=f'Top 10 Countries by Cumulative Medals in {selected_sport} ({selected_season}, {selected_year})',
        labels={'Cumulative Medals': 'Cumulative Number of Medals', 'Team': 'Country'},
        color_discrete_sequence=['#1f77b4'],  # Use the same color for all bars
        height=600
    )

    return fig





"""## Line charts function"""

def create_gdp_line_chart(df, selected_countries=None):
    # Set default to Israel if no countries are selected
    if selected_countries is None or len(selected_countries) == 0:
        selected_countries = ['ISR']  # Default to Israel's country code

    # Filter data for the selected countries
    filtered_data = df[df['country_code'].isin(selected_countries)]

    # Create GDP Line Chart
    fig = px.line(
        filtered_data,
        x='Year',
        y='GDP',
        color='Region',
        title='GDP Over the Years',
        labels={'GDP': 'GDP', 'Year': 'Year', 'Region': 'Country'},
    )

    return fig
def create_medal_line_chart(df, selected_countries=None):
    # Set default to Israel if no countries are selected
    if selected_countries is None or len(selected_countries) == 0:
        selected_countries = ['ISR']  # Default to Israel's country code

    # Filter data for the selected countries
    filtered_data = df[df['country_code'].isin(selected_countries)]

    # Create Cumulative Medals Line Chart
    fig = px.line(
        filtered_data,
        x='Year',
        y='Cumulative Medals',
        color='Region',
        title='Cumulative Medals Over the Years',
        labels={'Cumulative Medals': 'Cumulative Medals', 'Year': 'Year', 'Region': 'Country'},
    )

    return fig

"""## Dash code"""

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Layout of the Dash app
app.layout = html.Div(
    children=[
        # Header section with buttons and background color
        html.Div(
            style={
                'background-color': '#002366',
                'padding': '10px',
                'background-image': 'url("/assets/olympic_header5.png")',
                'background-repeat': 'no-repeat',
                'background-position': 'center',
                'background-size': '100% 150%',
                'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.2)',  # Add shadow for depth
                'height': '200px',
                'display': 'flex',  # Use flexbox
                'flex-direction': 'column',  # Arrange content vertically
                'justify-content': 'flex-end',  # Align items at the bottom
                'align-items': 'center',

            },
            children=[
                html.H1("Olympic Dashboard", style={'color': 'white', 'text-align': 'center', 'font-weight': 'bold', 'font-size': '36px'}),
                html.Div(
                    style={'display': 'flex', 'justify-content': 'center', 'gap': '20px'},
                    children=[
                        dbc.Button("GDP", id='gdp-button', color="primary", style={
                            'background-color': '#0052A5',
                            'border-color': '#0052A5',
                            'color': 'white',
                            'font-weight': 'bold',
                            'border-radius': '8px',  # Rounded corners
                            'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.2)',  # Shadow for buttons
                            'transition': 'background-color 0.3s ease'
                        }, outline=False),
                        dbc.Button("Summer Olympics", id='summer-button', color="primary", style={
                            'background-color': '#0052A5',
                            'border-color': '#0052A5',
                            'color': 'white',
                            'font-weight': 'bold',
                            'border-radius': '8px',
                            'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.2)',
                            'transition': 'background-color 0.3s ease'
                        }, outline=False),
                        dbc.Button("Winter Olympics", id='winter-button', color="primary", style={
                            'background-color': '#0052A5',
                            'border-color': '#0052A5',
                            'color': 'white',
                            'font-weight': 'bold',
                            'border-radius': '8px',
                            'box-shadow': '0 2px 4px rgba(0, 0, 0, 0.2)',
                            'transition': 'background-color 0.3s ease'
                        }, outline=False),
                    ]
                )
            ]
        ),


        # GDP Modal
        dbc.Modal(
            [
                dbc.ModalHeader("What is GDP?"),
                dbc.ModalBody("GDP, or Gross Domestic Product, is a measure of the total value of all goods and services produced within a country over a specific period, usually a year. It is a key indicator used to gauge the health of a country's economy. A higher GDP typically means a stronger economy, while a lower GDP indicates a weaker one."),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-gdp-modal", className="ml-auto", n_clicks=0)
                ),
            ],
            id="gdp-modal",
            is_open=False,
        ),

        # Summer Olympics Modal
        dbc.Modal(
            [
                dbc.ModalHeader("What are the Summer Olympics?"),
                dbc.ModalBody("The Summer Olympics is a global multi-sport event that occurs every four years, usually during July or August. It brings together athletes from around the world to compete in a wide range of sports, including swimming, athletics, gymnastics, basketball, football (soccer), tennis, cycling, and many more. The event celebrates athletic excellence and promotes international unity."),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-summer-modal", className="ml-auto", n_clicks=0)
                ),
            ],
            id="summer-modal",
            is_open=False,
        ),

        # Winter Olympics Modal
        dbc.Modal(
            [
                dbc.ModalHeader("What are the Winter Olympics?"),
                dbc.ModalBody("The Winter Olympics is an international multi-sport event that takes place every four years, typically in February. It features sports that are primarily played on snow and ice, including skiing, snowboarding, ice hockey, figure skating, bobsledding, and curling. The Winter Olympics highlight the skills and endurance of athletes in cold-weather sports and foster global camaraderie."),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-winter-modal", className="ml-auto", n_clicks=0)
                ),
            ],
            id="winter-modal",
            is_open=False,
        ),

        # Scatter plot section with filter in a "cube"
        html.Div(
            style={'padding': '30px', 'border': '1px solid #ccc', 'margin-top': '20px', 'background-color': '#f4f4f4', 'border-radius': '10px', 'border-left': '5px solid #0052A5'},
            children=[
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            dbc.Label("Select Countries", html_for="country-selector"),
                            dcc.Dropdown(
                                id='country-selector',
                                options=[{'label': country, 'value': code} for country, code in country_name_to_code.items()],
                                multi=True,
                                placeholder="Select countries to display",
                                style={'margin-bottom': '20px'}
                            ),
                        ]),
                        width=3,
                    ),
                    dbc.Col(
                        dcc.Graph(id='gdp-medals-scatter', style={'height': '600px', 'width': '100%'}),
                        width=9,
                    )
                ]),
            ]
        ),

        # Line charts section with filters in a "cube"
        html.Div(
            style={'padding': '10px', 'border': '1px solid #ccc', 'margin-top': '13px', 'background-color': '#f4f4f4', 'border-radius': '10px', 'border-left': '5px solid #d9534f'},
            children=[
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            dbc.Label("Select Country", html_for="linechart-country-selector"),
                            dcc.Dropdown(
                                id='linechart-country-selector',
                                options=[{'label': country, 'value': code} for country, code in country_name_to_code.items()],
                                value='ISR',
                                multi=False,
                                placeholder="Select a country for line charts",
                                style={'margin-bottom': '5px'}
                            ),
                        ]),
                        width=12
                    )
                ]),
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id='gdp-line-chart', style={'height': '600px'}),
                        width=6
                    ),
                    dbc.Col(
                        dcc.Graph(id='medal-line-chart', style={'height': '600px'}),
                        width=6
                    )
                ]),
            ]
        ),

        # Bar plot section with filters in a "cube"
        html.Div(
            style={'padding': '30px', 'border': '1px solid #ccc', 'margin-top': '20px', 'background-color': '#f4f4f4', 'border-radius': '10px', 'border-left': '5px solid #5bc0de'},
            children=[
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            dbc.Label("Select Season", html_for="barplot-season-selector"),
                            dcc.Dropdown(
                                id='barplot-season-selector',
                                options=[
                                    {'label': 'Summer', 'value': 'Summer'},
                                    {'label': 'Winter', 'value': 'Winter'}
                                ],
                                value='Summer',
                                clearable=False,
                                style={'margin-bottom': '20px'}
                            ),
                            dbc.Label("Select Sport", html_for="barplot-sport-selector"),
                            dcc.Dropdown(
                                id='barplot-sport-selector',
                                placeholder="Select a sport",
                                value='Football',
                                style={'margin-bottom': '20px'}
                            ),
                            dbc.Label("Select Year", html_for="barplot-year-selector"),
                            dcc.Dropdown(
                                id='barplot-year-selector',
                                placeholder="Select a year",
                                value=1960,
                                style={'margin-bottom': '20px'}
                            ),
                        ]),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Graph(id='medal-bar-plot', style={'height': '600px', 'width': '100%'}),
                        width=9
                    ),
                ]),
            ]
        ),

        # Map section with filters in a "cube"
        html.Div(
            style={'padding': '30px', 'border': '1px solid #ccc', 'margin-top': '20px', 'background-color': '#f4f4f4', 'border-radius': '10px', 'border-left': '5px solid #f0ad4e'},
            children=[
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            dbc.Label("Select Season", html_for="season-selector"),
                            dcc.Dropdown(
                                id='season-selector',
                                options=[
                                    {'label': 'Summer', 'value': 'Summer'},
                                    {'label': 'Winter', 'value': 'Winter'}
                                ],
                                value='Summer',
                                clearable=False,
                                style={'margin-bottom': '20px'}
                            ),
                            dbc.Label("Select Medals", html_for="medal-filter"),
                            dbc.Checklist(
                                id='medal-filter',
                                options=[
                                    {'label': 'Gold', 'value': 'Gold'},
                                    {'label': 'Silver', 'value': 'Silver'},
                                    {'label': 'Bronze', 'value': 'Bronze'}
                                ],
                                value=['Gold', 'Silver', 'Bronze'],
                                inline=True,
                                style={'padding': '10px', 'margin-bottom': '20px'}
                            ),
                        ]),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Graph(id='medal-map', style={'height': '600px', 'width': '100%'}),
                        width=9
                    ),
                ]),
            ]
        )
    ]
)
# Callbacks for updating the visualizations
@app.callback(
    Output('medal-map', 'figure'),
    [Input('season-selector', 'value'), Input('medal-filter', 'value')]
)
def update_map(selected_season, selected_medals):
    return create_map(medals_per_country, selected_season, selected_medals)

@app.callback(
    Output('gdp-medals-scatter', 'figure'),
    [Input('country-selector', 'value')]
)
def update_animated_scatter(selected_countries):
    if not selected_countries:
        filtered_data = combined_data_cleaned
    else:
        filtered_data = combined_data_cleaned[combined_data_cleaned['country_code'].isin(selected_countries)]
    return create_animated_scatter_plot(filtered_data)

@app.callback(
    Output('barplot-sport-selector', 'options'),
    [Input('barplot-season-selector', 'value')]
)
def update_sport_options(selected_season):
    sports = athlete_data[athlete_data['Season'] == selected_season]['Sport'].unique()
    return [{'label': sport, 'value': sport} for sport in sports]

@app.callback(
    Output('barplot-year-selector', 'options'),
    [Input('barplot-season-selector', 'value'),
     Input('barplot-sport-selector', 'value')]
)
def update_year_options(selected_season, selected_sport):
    years = athlete_data[(athlete_data['Season'] == selected_season) &
                         (athlete_data['Sport'] == selected_sport)]['Year'].unique()
    return [{'label': str(year), 'value': year} for year in sorted(years)]

@app.callback(
    Output('medal-bar-plot', 'figure'),
    [Input('barplot-sport-selector', 'value'),
     Input('barplot-season-selector', 'value'),
     Input('barplot-year-selector', 'value')]
)
def update_bar_plot(selected_sport, selected_season, selected_year):
    return create_medal_bar_plot(athlete_data, selected_sport, selected_season, selected_year)

# Callback for updating the line charts with a single country filter
@app.callback(
    [Output('gdp-line-chart', 'figure'),
     Output('medal-line-chart', 'figure')],
    [Input('linechart-country-selector', 'value')]
)
def update_line_charts(selected_country):
    if not selected_country:
        return {}, {}
    gdp_fig = create_gdp_line_chart(combined_data_cleaned, [selected_country])
    medal_fig = create_medal_line_chart(combined_data_cleaned, [selected_country])
    return gdp_fig, medal_fig

# Callback to manage the modal state
@app.callback(
    [dash.dependencies.Output(f"{button}-modal", "is_open") for button in ["gdp", "summer", "winter"]],
    [dash.dependencies.Input(f"{button}-button", "n_clicks") for button in ["gdp", "summer", "winter"]] +
    [dash.dependencies.Input(f"close-{button}-modal", "n_clicks") for button in ["gdp", "summer", "winter"]],
    [dash.dependencies.State(f"{button}-modal", "is_open") for button in ["gdp", "summer", "winter"]]
)
def toggle_modal(gdp_open, summer_open, winter_open, gdp_close, summer_close, winter_close, gdp_is_open, summer_is_open, winter_is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [False, False, False]

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'gdp-button' or button_id == 'close-gdp-modal':
        return [not gdp_is_open, False, False]
    elif button_id == 'summer-button' or button_id == 'close-summer-modal':
        return [False, not summer_is_open, False]
    elif button_id == 'winter-button' or button_id == 'close-winter-modal':
        return [False, False, not winter_is_open]
    return [False, False, False]

# Run the app
if __name__ == '__main__':
    # output.serve_kernel_port_as_window(8050)
    app.run_server(debug=False,port  = 8053)

