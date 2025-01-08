import json
import os.path

import requests
from dataclasses import dataclass

from importlib_metadata import distribution
from requests.models import Response

from rdf_objects.dcat_distribution import DcatDistribution
from tools.error_handler import *
from flask import make_response
from data_objects.asset_object import *
import re
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import DCTERMS, DCAT, RDF, XSD
from util import get_logger

logger = get_logger('data_layer')

@dataclass(frozen=True)
class DataStorage:
    _uri: str

    # headers = {
    #     'Authorization': "3yF8!oNEzR2/bHDx*WU#F@^pLM9NQa6"
    # }

    # def get_filenames(self, access_token_cookies:str, access_token_headers:str) -> Response:
    #     headers = {
    #         'Authorization': access_token_headers
    #     }
    #     cookies = {
    #         'access_token': access_token_cookies
    #     }
    #     params = {
    #         'asset_type': 'File'
    #     }

    #     response = requests.get(self._uri + '/assets/get_all_names', headers=headers, cookies=cookies, params=params)

    #     return response

    def get_asset_tabular(self, asset_uuid: str, access_token_cookies: str, auth_token: str) -> Response:
        headers = {
            'Authorization': auth_token
        }
        cookies = {
            'access_token': access_token_cookies
        }
        args = {
            'asset_uuids': [asset_uuid]
        }

        response = requests.post(self._uri + '/assets', headers=headers, cookies=cookies, json=args)

        return response

    
## TODO: Change with endpoint spec
    def get_asset_file(self, file_uuid:str, access_token_cookies:str, auth_token:str) -> Response:
        # print("data_layer.py - get_asset_file", flush=True)
        headers = {
            'Authorization': auth_token
        }
        # cookies = {
        #     'access_token': access_token_cookies
        # }
        args = {
            'asset_uuid': file_uuid
            # 'asset_type': 'File'
        }

        response = requests.get(self._uri + '/api/files/get_file', headers=headers, cookies=None, params=args)
        # print(response, flush=True)

        return response

    def create_table(self, file_distribution_id: str, asset: Asset, access_token_cookies: str, access_token: str) -> Response:
        headers = {
            'Authorization': access_token,
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'file_distribution_id': file_distribution_id,
        }

        response = requests.post(
            self._uri + '/api/tables/create_table',
            headers=headers,
            cookies=None,
            json=asset.model_dump()
        )

        logger.debug(f"Factory Data Storage - create_table response:\n{response}\n{response.text}")

        return response


@dataclass(frozen=True)
class DataModelRepository:
    _uri: str

    def load_datamodel(self, access_token_cookies: str, access_token_headers: str):
        # headers = {
        #     'Authorization': access_token_headers
        # }
        # cookies = {
        #     'access_token': access_token_cookies
        # }

        # TODO: let user select the data model
        model_id = '65c33849-0fa5-46e7-970b-56b774f57e3b'
        response = requests.get(f'https://pistis-market.eu/srv/models-repository/api/models/{model_id}/download')

        return response

    def search_properties(self, sequence: str, properties: list) -> dict:
        pattern = re.compile(sequence, re.IGNORECASE)
        search_results = list(
            filter(lambda property_: len(pattern.findall(property_['name'])) > 0 and property_["name"] != "null",
                   properties))

        return {
            'properties': search_results
        }


@dataclass(frozen=True)
class MetadataCatalogue:
    _uri: str
    headers = {
        'X-API-Key': "b857b3c5-ccc4-4e1d-b378-32c6b879942d"
    }

    def get_metadata(self, metadata_id: str):
        url = self._uri + 'datasets/' + metadata_id
        logger.debug(f"Metadata Catalogue - get_metadata (URI: {url})")

        response = requests.get(url)
        logger.debug(f"Metadata Catalogue - response: {response}")

        return response

    def create_metadata(self, metadata_id, metadata: MetaData):
        url = self._uri + 'datasets/' + metadata_id
        logger.debug(f"Metadata Catalogue - create_metadata (URI: {url})")

        response = requests.put(url, headers=self.headers, data=metadata.serialize())

        return response

    def build_graph(self, metadata_object: str):

        g = Graph()
        g.parse(data=metadata_object, format='json-ld')

        # Print the RDF graph in Turtle format
        print("TURTLE GRAPH-------------------------------------------------------------- \n\n", flush=True)

        print(g.serialize(format='turtle'), flush=True)

        return g

    def update_accessURL(self, uuid: str, g, metadata_id):

        access_url = DCAT.accessURL
        # asset_uuid = uuid
        ##TODO: Build the access url

        new_access_url = URIRef(
            f"https://develop.pistis-market.eu/srv/factory-data-storage/api/tables/get_table?asset_uuid={uuid}")
        # new_access_url = URIRef("https://test-url-from-enrichment.com")

        for s, p, o in g.triples((None, access_url, None)):
            if p == access_url:
                # Remove the old triple
                g.remove((s, p, o))
                # Add the new triple with the updated accessURL
                g.add((s, p, new_access_url))
                print(f"Updated accessURL for subject {s} to {new_access_url}")

        # # Print the RDF graph in Turtle format
        print("UPDATED ACCESSURL GRAPH-------------------------------------------------------------- \n\n", flush=True)
        print(g.serialize(format='turtle'), flush=True)

        # response = requests.put(self._uri + f'{metadataId}', headers=self.headers)
        return g

    def get_distribution(self, distribution_id: str):
        url = self._uri + 'distributions/' + distribution_id
        logger.debug(f"Metadata Catalogue - get_distribution (URI: {url})")

        response = requests.get(url)
        logger.debug(f"Metadata Catalogue - response: {response}")

        return response

    def add_distribution(self, dataset_id, distribution: DcatDistribution, auth_token: str):
        """
        Add a distribution to a dataset in the metadata catalogue.
        """

        # Construct the endpoint URL
        url = f"{self._uri}datasets/{dataset_id}/distributions"

        # Prepare headers
        headers = {
            'Authorization': auth_token,
            'Content-Type': 'text/turtle',
            'X-API-Key': self.headers['X-API-Key']
        }

        # Prepare the data
        data = distribution.serialize(rdf_format='turtle')

        # Make the request
        response = requests.post(url, headers=headers, data=data)

        return response

# ## TODO: Update with PISTIS IAM
# @dataclass(frozen=True)
# class IdentityManager():
#     _uri:str

#     def authorize(self, access_token_cookies:str, access_token_headers:str):
#         headers = {
#             'Authorization': access_token_headers
#         }
#         cookies = {
#             'access_token': access_token_cookies
#         }

#         response = requests.get(self._uri + '/verify', headers=headers, cookies=cookies)

#         if response.status_code == 200:
#             pass

#         elif response.status_code == 401:
#             raise CustomError(
#                 'Unauthorized Access!',
#                 'DATA ENRICHMENT',
#                 401
#             )

#         else:
#             raise CustomError(
#                 'The Identity Manager returned an invalid response!',
#                 'IDENTITY MANAGER',
#                 502,
#                 response.text
#             )

@dataclass(frozen=True)
class Search:
    _uri: str

    def search_dataset(self, dataset_id: str):
        url = self._uri + 'datasets/' + dataset_id
        logger.debug(f"Search - search_dataset (dataset_id: {url})")

        response = requests.get(url)
        logger.debug(f"Search - response: {response}")

        return response