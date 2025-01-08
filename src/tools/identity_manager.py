#identity_manager.py

import uuid, requests,json, os
from flask import make_response,jsonify
from functools import lru_cache
from dataclasses import dataclass
import jwt
#from keycloak import KeycloakOpenID ## TODO: Check the library and rewrite the class

KEYCLOAK_URL = os.getenv('KEYCLOAK','https://auth.pistis-market.eu/auth/realms/PISTIS/protocol/openid-connect/token')
AUTHENTICATION_ID = os.getenv('DATA_ENRICHMENT_BACKEND_ID','pistis-test-only')
AUTHENTICATION_SECRET = os.getenv('DATA_ENRICHMENT_BACKEND_SECRET','DYuAlXn8kC1SVzFiYgApfjcodZhdxreL')

@dataclass
class IdentityManager():
    content_type: str
    grant_type: str
    permission : str


class IdentityManagerApi():

    def service_account_authenticate(self,keycloak_object):
        
        headers = {
            'Content-Type': keycloak_object.content_type
        }
        keycloak_request = {
            'grant_type': keycloak_object.grant_type,
            'client_id': AUTHENTICATION_ID,
            'client_secret': AUTHENTICATION_SECRET
        }

        keycloak_response = requests.post(KEYCLOAK_URL, headers=headers, data=keycloak_request)

        return keycloak_response
    
    
    def user_account_authenticate(self,keycloak_object):

        headers = {
            'Content-Type': keycloak_object.content_type
        }
        keycloak_request = {
            'grant_type': keycloak_object.grant_type,
            'client_id': AUTHENTICATION_ID,
            'client_secret': AUTHENTICATION_SECRET,
            'username': "00-test",
            'password': "00-test"
        }

        keycloak_response = requests.post(KEYCLOAK_URL, headers=headers, data=keycloak_request)

        return keycloak_response


   
    def user_account_authorize(self,keycloak_object,access_token):
        
        headers = {
            'Content-Type': keycloak_object.content_type,
            'Authorization': f'Bearer {access_token}'
        }
        keycloak_request = {
            'grant_type': keycloak_object.grant_type,
            'audience': 'resource-server'
        }
        ##TODO: Add permission key if dataset id can be checked
        keycloak_response = requests.post(KEYCLOAK_URL, headers=headers, data=keycloak_request)
        # print(keycloak_response.text, flush=True)
        if keycloak_response.status_code == 200:
            encoded_jwt = keycloak_response.json()["access_token"]
            # Decode the JWT without verifying the signature
            decoded_jwt = jwt.decode(encoded_jwt, options={"verify_signature": False})
            # print(decoded_jwt["authorization"], flush=True)
            ## TODO: Check for ids in authorization and check if the permission matches 
        return keycloak_response
    

    def jwt_decode(self,access_token):
        
        decoded_jwt = jwt.decode(access_token, options={"verify_signature": False})
        # print(decoded_jwt, flush=True)

        ##TODO: Why is the group a list ? Is username preferred username or role?
        userGroup = decoded_jwt["group"]
        if not userGroup:
            userGroup = "service-account"
        else:
            userGroup = userGroup[0]
        decoded_object = {
            'username': decoded_jwt["preferred_username"],
            'usergroup': userGroup
        }
        # print(decoded_object, flush=True)
        return decoded_object