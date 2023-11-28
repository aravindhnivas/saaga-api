import requests
import os
from seed_payload import species_payload_list
token = os.environ.get('TOKEN')
species_post_url = "http://127.0.0.1:8000/api/data/species/"
for species_payload in species_payload_list:
    requests.post(species_post_url, headers={
                  'Authorization': token}, data=species_payload)
