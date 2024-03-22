import googlemaps
import time

from config import GMAPS_API

## Establish API Connection
gmaps = googlemaps.Client(key=GMAPS_API)

## Find places
geocode = gmaps.geocode('Rua Caldas, 660, Vila Cristina, Betim - MG')
results = gmaps.places(
    query='padaria', 
    location=geocode[-1].get('geometry').get('location'), 
    radius=1500)
data = []
data.append(results)
print('Primeiro registro == ', data[-1].get('results')[-1].get('name'))
while results.get('next_page_token'):
    print('Dentro do loop 1 == ', data[-1].get('results')[-1].get('name'))
    time.sleep(3)
    page_token = results.get('next_page_token')
    results = gmaps.places(page_token=page_token)
    data.append(results)
    print('Depois de pegar os dados 2 == ', data[-1].get('results')[-1].get('name'))