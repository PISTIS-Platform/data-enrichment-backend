import os
import unittest
import requests

DATA_ENRICHMENT_URL = os.getenv("DATA_ENRICHMENT_URL", "http://127.0.0.1:8080")

# Authentication
GRANT_TYPE = os.getenv("GRANT_TYPE", "password")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")



def get_auth_token():
    header = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': GRANT_TYPE,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': USERNAME,
        'password': PASSWORD
    }
    response = requests.post("https://auth.pistis-market.eu/auth/realms/PISTIS/protocol/openid-connect/token", headers=header, data=data)
    return "Bearer " + response.json()["access_token"]

BEARER_TOKEN = get_auth_token()