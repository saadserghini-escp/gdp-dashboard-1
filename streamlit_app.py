import streamlit as st
import pandas as pd
import math
from pathlib import Path
from PIL import Image
import base64
from io import BytesIO
import altair as alt

# -----------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE

st.set_page_config(
    page_title='Arabic countries GDP dashboard',
    page_icon=':earth_africa:'
)

st.markdown("<style>div.block-container {padding-top: 1rem;}</style>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# LOGO EN HAUT À DROITE

logo = Image.open("data/logo.png")
buffered = BytesIO()
logo.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()

col1, col2 = st.columns([5, 1])
with col2:
    st.markdown(
        f"<div style='padding-top: 40px'><img src='data:image/png;base64,{img_b64}' width='250'></div>",
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# FONCTION POUR CHARGER LES DONNÉES

@st.cache_data
def get_gdp_data():
    DATA_FILENAME = Path(__file__).parent / 'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    if 'Value' in raw_gdp_df.columns:
        raw_gdp_df = raw_gdp_df.rename(columns={'Value': 'GDP'})

    raw_gdp_df['Year'] = pd.to_numeric(raw_gdp_df['Year'], errors='coerce')
    gdp_df = raw_gdp_df[['Country Name', 'Country Code', 'Year', 'GDP']]
    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# TITRE

st.markdown("# :earth_africa: Arabic Countries GDP dashboard")

st.markdown("<p style='font-size:12px'>by Saad Serghini</p>", unsafe_allow_html=True)

st.markdown('''
Browse GDP data for all Arabic countries based on the [World Bank Open Data](https://data.worldbank.org/). Data range goes from 1960 to 2022, but some GDP's could be missing.
''')

''
''

# -----------------------------------------------------------------------------
# SLIDER ET SÉLECTION DE PAYS

min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Choose your data range:',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value]
)

countries = gdp_df['Country Code'].unique()

selected_countries = st.multiselect(
    'Which country(ies) would you like to view?',
    countries,
    ['MAR', 'DZA', 'LBN', 'TUN', 'EGY']
)

# -----------------------------------------------------------------------------
# GRAPHIQUE INTERACTIF

filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries)) &
    (gdp_df['Year'] >= from_year) &
    (gdp_df['Year'] <= to_year)
]

st.header('GDP over time', divider='gray')

if not filtered_gdp_df.empty:
    filtered_gdp_df = filtered_gdp_df.dropna(subset=["GDP"])
    filtered_gdp_df["Year"] = pd.to_numeric(filtered_gdp_df["Year"], errors="coerce")
    filtered_gdp_df["GDP"] = pd.to_numeric(filtered_gdp_df["GDP"], errors="coerce")

    hover = alt.selection_point(fields=["Year"], nearest=True, on="mouseover", empty="none")

    base = alt.Chart(filtered_gdp_df).encode(
        x=alt.X("Year:Q", title="Year", axis=alt.Axis(format="d")),
        y=alt.Y("GDP:Q", title="GDP"),
        color=alt.Color("Country Code:N", title="Country")
    )

    lines = base.mark_line()
    points = base.mark_circle(size=65).transform_filter(hover).encode(
        tooltip=["Country Name:N", "Year:Q", "GDP:Q"]
    )
    rule = base.mark_rule(color="gray").encode(tooltip=["Year:Q"]).add_params(hover)

    chart = (lines + points + rule).interactive().properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.warning("No data available for this selection.")

# -----------------------------------------------------------------------------
# MÉTRIQUES GDP

first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

has_data = any(
    not gdp_df[
        (gdp_df['Country Code'] == code) &
        (gdp_df['Year'] >= from_year) &
        (gdp_df['Year'] <= to_year)
    ].dropna(subset=['GDP']).empty
    for code in selected_countries
)

if not has_data:
    st.warning("No data available for this selection.")

cols = st.columns(4)
for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]
    with col:
        country_data = gdp_df[
            (gdp_df['Country Code'] == country) &
            (gdp_df['Year'] >= from_year) &
            (gdp_df['Year'] <= to_year)
        ].dropna(subset=['GDP']).sort_values('Year')

        if country_data.empty:
            st.metric(label=f'{country} GDP', value='n/a', delta='n/a', delta_color='off')
            continue

        first_gdp_raw = country_data.iloc[0]['GDP']
        exact_year_data = country_data[country_data['Year'] == to_year]

        if exact_year_data.empty:
            st.metric(label=f'{country} GDP', value='n/a', delta='n/a', delta_color='off')
            continue

        last_gdp_raw = exact_year_data.iloc[0]['GDP']
        first_gdp = first_gdp_raw / 1e9
        last_gdp = last_gdp_raw / 1e9
        growth = f'{last_gdp / first_gdp:,.2f}x'
        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color='normal'
        )

# -----------------------------------------------------------------------------
# NEWS PAR PAYS

st.header("📰 GDP News for selected countries", divider='gray')

selected_country_names = gdp_df[gdp_df['Country Code'].isin(selected_countries)]['Country Name'].unique()

if len(selected_country_names) == 0:
    st.warning("No news to show for this selection.")
else:
    for country in selected_country_names:
        search_query = f"{country} GDP site:news.google.com"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        st.markdown(f"🔎 [News about **{country} GDP**](<{search_url}>)", unsafe_allow_html=True)
