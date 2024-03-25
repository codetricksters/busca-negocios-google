import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path, PurePosixPath, PureWindowsPath
from datetime import datetime, timezone
import googlemaps
import tomli
# Folium map
import folium
from streamlit_folium import st_folium
from config import GMAPS_API
import time


st.set_page_config(layout='wide')
st.title(f'Pesquisa de negócios {datetime.now(timezone.utc)}')

if Path('apiconfig.toml').is_file():
    with open('apiconfig.toml', 'rb') as fc:
        apiconfig = tomli.load(fc)

columns = apiconfig['table']['columns']
gmaps = googlemaps.Client(key=GMAPS_API) # 'Add Your Key here'

@st.cache_data
def generate_map(coords: tuple) -> folium:
    map = folium.Map(location=midpoint, zoom_start=10)
    st.header('Folium map')
    return st_folium(map, width=800)

@st.cache_data
def places(query:str='', location:str='') -> pd.DataFrame:
    geocode = gmaps.geocode(location)
    ## Find places
    response = gmaps.places(
                           query=query, 
                           location=geocode[-1].get('geometry').get('location'), 
                           radius=1000, 
                           language = 'pt-BR'
                           )
    data = []
    data.append(response)

    while response.get('next_page_token'):
        time.sleep(3)
        page_token = response.get('next_page_token')
        response = gmaps.places(page_token=page_token)
        data.append(response)

    df = pd.json_normalize(data, record_path='results')
    return df

@st.cache_data
def place_details(place_id):
    response = gmaps.place(place_id=place_id, language='pt-BR')
    df = pd.json_normalize(response.get('result'))
    return df


def search(query, location):
    try:
        df = places(query=query, location=location)
        df.rename(columns={'geometry.location.lat': 'lat', 'geometry.location.lng':'lon'}, inplace=True)
        # Adding code so we can have map default to the center of the data
        places_details = []
        with st.spinner('Coletando dados....'):
            for index, place in df.iterrows():
                details = place_details(place['place_id'])
                places_details.append(details)

        p = pd.concat(places_details)
        # st.dataframe(p[columns])
        midpoint = (np.average(df['lat']), np.average(df['lon']))
        # st.map(df, latitude='lat', longitude='lon',size=35, zoom=12)
        st.session_state.clicked = True
        return p[columns]

    except Exception as e:
        st.warning(f'{type(e).__name__}, {e}')

if 'clicked' not in st.session_state:
    st.session_state.clicked = False

st.caption("""Use endereços com muita informação, por exemplo 
          _"Alameda Oscar Niemeyer, 132 - Vale do Sereno, Nova Lima - MG, 34006-049"_.
            Informações como bairro e cidade são obrigatórias para um bom resultado'
          """)
query = st.text_input('Tipo')
location = st.text_input(label='Endereço')

if len(location) < 1 and len(query) < 1:
    st.error('Informe um endereço e tipo de negócio para começar a pesquisa')

st.button('Pesquisa', on_click=search, args=[query, location])

if st.session_state.clicked and len(location) > 0 and len(query) > 0:
    df = search(query, location)
    map = folium.Map(location=df[['geometry.location.lat', 'geometry.location.lng']].iloc[0].to_list(), zoom_start=15)
    st.dataframe(df)
    for _,row in df.fillna('').iterrows():
        popup = f"""
            {row["name"]}, 
            {row["formatted_address"]}, 
            {row["formatted_phone_number"]},
            {row["business_status"]}
        """
        folium.Marker(
            [row['geometry.location.lat'], row['geometry.location.lng']],
            popup=folium.Popup(popup, parse_html=True, max_width=200),
            tooltip=row['name']
            ).add_to(map) 
    map_data = st_folium(map, use_container_width=True)
