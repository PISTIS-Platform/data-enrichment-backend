import os
import json
from typing import Dict
from datetime import datetime, timezone
from rdflib import Graph, URIRef
from tools.error_handler import *
from flask import make_response

from data_layer import *
from data_objects.asset_object import *
from rdf_objects.dcat_distribution import CsvwColumn, DcatDistribution
from tools.file_parser import *
from cache.cache import *
from util import get_logger


logger = get_logger('logic_layer')
cache = Cache('cache/CACHE.db')

## TODO: Update URIs
data_storage = DataStorage(os.getenv('DATA_STORE_URI', 'https://develop.pistis-market.eu/srv/factory-data-storage/'))
datamodel_repository = DataModelRepository(os.getenv('DATAMODEL_REPO_URI', 'https://pistis-market.eu/srv/models-repository'))
metadata_catalogue = MetadataCatalogue(os.getenv('METADATA_CATALOGUE_URI', 'https://develop.pistis-market.eu/srv/repo/'))
search = Search(os.getenv('SEARCH_URI', 'https://develop.pistis-market.eu/srv/search/'))

## TODO: Update once Data model repository is live
# def update_kgm_properties(access_token_cookies:str, access_token_headers:str) -> Response:
#     my_response = datamodel_repository.load_datamodel(access_token_cookies=access_token_cookies, access_token_headers=access_token_headers)
#     if my_response.status_code == 200:
#         kg = my_response.json()
#         properties = {
#             'properties':[{'name': node['label'], 'dataType': node['dataType'], 'propertyID': node['id']} for node in kg['nodes'] if node['type'] == 'Property']
#         }
#         cache.update_kgm_properties(properties)

#         my_response._content = json.dumps({
#             'message': 'KGM data model updated successfully!'
#         }).encode('utf-8')
        
#         return my_response

#     else:
#         raise CustomError(
#                         'GatewayError: The Knowledge Graph Manager returned an invalid response!',
#                         'KNOWLEDGE GRAPH MANAGER',
#                         502,
#                         my_response.text
#                     )    

def livesearch(sequence:str, access_token_cookies:str, access_token_headers:str) -> Response:
    try:
        # properties = cache.get_properties()
        # datamodel = datamodel_repository.load_datamodel(access_token_cookies=access_token_cookies, access_token_headers=access_token_headers)

        # Get data model from file
        # data_model = rdf_to_json("data_models/combined_data_models.rdf")
        with open('data_models/combined_data_model.json', 'r') as file:
            data_model = json.load(file)
        # print("DATA MODEL: ", data_model)

        # search_results = datamodel_repository.search_properties(sequence, datamodel.json()["properties"])
        search_results = datamodel_repository.search_properties(sequence, data_model["properties"])
        # print("Search results: ", search_results)

        return search_results

    except IndexError:
        raise CustomError(
            'No datamodel provided. Please update the  datamodel!',
            'DATA ENRICHMENT BACKEND',
            500
            )

    # except TypeError:
    #     raise CustomError(
    #         'The sequence must be provided as a String!',
    #         'DATA ENRICHMENT BACKEND',
    #         400
    #         )


def retrieve_file(dataset_id: str, distribution_id: str, file_type: str, access_token_cookies: str, auth_token: str) -> Response:
    """
    Retrieve a file from the data storage using the distribution id and convert it to an Asset object.
    """

    # Get the asset id from the distribution
    logger.debug(f"Fetching asset id for distribution id: {distribution_id}")
    try:
        # Fetch the distribution from the metadata catalogue
        distributions = get_distributions(dataset_id)

        logger.debug(f"Response json: {json.dumps(distributions, indent=2)}")
        # Extract the access URL from the distribution

        access_url = None
        for dist in distributions:
            if dist['id'] == distribution_id:
                access_urls = dist.get('access_url', None)
                if len(access_urls) > 0:
                    access_url = access_urls[0]
                    break

        logger.debug(f"The access URL for distribution id {distribution_id} is: {access_url}")
        if access_url is None:
            raise CustomError(
                'No access URL found in the distribution!',
                'Metadata Catalogue',
                404
            )

        # Since the factory data storage expects the asset id instead of the whole access url,
        # extract the asset id from the access URL
        asset_id = access_url.split('asset_uuid=')[-1]
    except Exception as e:
        raise CustomError(
            f'Unable to retrieve asset id from distribution: {e}',
            'FILE DATA HARVESTER BACKEND',
            404
        )

    # Retrieve the file from the data storage
    logger.debug(f"Retrieving file with asset id: {asset_id}")

    if file_type is not None:
        my_response = data_storage.get_asset_file(file_uuid=asset_id, access_token_cookies=access_token_cookies, auth_token=auth_token)
        logger.debug("File type: " + file_type)
        logger.debug("Response status code: " + str(my_response.status_code))
        logger.debug("Response text: " + my_response.text)
        if my_response.status_code == 200:
            logger.debug(f"File with UUID: {asset_id} retrieved successfully. Decoding ...")

            if file_type == 'xls':
                text = excelToCSV(my_response.content)
            elif file_type == 'json':
                text = jsonToCSV(my_response.content)
            else:
                text = my_response.content.decode('utf-8-sig')

            logger.debug("Converting text to asset object ...")
            asset, asset_preview = csvAndTxtToAsset(text)

            logger.debug("Storing asset in cache ...")
            cache.store_asset(asset, distribution_id, True)

            logger.debug("Serializing asset ...")
            my_response._content = asset_preview.model_dump_json().encode('utf-8')

            print("Done!")
            return my_response

        else:
            raise CustomError(
                'GatewayError: The Data Storage returned an invalid response!',
                'Data Storage',
                502,
                my_response.text
            )
        
    else:
        ##TODO: Maybe tables do not have to be fetched
        my_response = data_storage.get_asset_tabular(asset_uuid=asset_id, access_token_cookies=access_token_cookies, auth_token=auth_token)
        if my_response.status_code == 200:
            asset = Asset.model_validate_json(my_response.json()[0])
            cache.store_asset(asset, asset_id, False)
            my_response._content = asset.model_dump_json().encode('utf-8')

            return my_response

        else:
            raise CustomError(
                'GatewayError: The Data Storage returned an invalid response!',
                'Data Storage',
                502,
                my_response.text
            )


def create_asset(dataset_id: str, distribution_id: str, metadata: MetaData, data_model: DataModel, access_token_cookies: str, access_token: str) -> Response:
    """
    Update the metadata and data model of an asset in the data storage.
    Check the response from the data storage and delete the asset from the cache if the update was successful.
    If the update was not successful (response code is not 200), raise an error.
    """

    try:
        # Retrieve the asset from the cache by its UUID
        logger.debug(f"Retrieving asset from cache with distribution id: {distribution_id}")
        asset, from_file = cache.get_asset(distribution_id)

        file_distribution_id = distribution_id if from_file else None

        # Add the metadata and data model to the asset
        asset.metadata = metadata
        logger.debug(f"Asset metadata: {asset.metadata}")
        asset.data_model = data_model
        logger.debug(f"Asset data model: {asset.data_model}")

        # Update the asset in the data storage
        logger.debug(f"Creating new table in the data storage for asset with UUID: {distribution_id}")
        response = data_storage.create_table(
            file_distribution_id=file_distribution_id,
            asset=asset,
            access_token_cookies=access_token_cookies,
            access_token=access_token,
        )
        access_url = response.json()['asset_uuid']
        print("Access URL: ", access_url)
    except Exception as e:
        raise CustomError(
            f'Failed to create asset: {e}',
            'DATA STORAGE',
            500
        )

    # Create a distribution in the metadata catalogue for the new asset
    try:
        logger.debug(f"Creating new distribution in the metadata catalogue for asset with UUID: {distribution_id}")
        add_distribution(
            dataset_id=dataset_id,
            from_distribution_id=distribution_id,
            access_url=f"https://develop.pistis-market.eu/srv/factory-data-storage/api/files/get_file?asset_uuid={access_url}",
            data_model=asset.data_model,
            auth_token=access_token
        )
    except Exception as e:
        raise CustomError(
            f'Failed to create distribution for the asset: {e}',
            'METADATA CATALOGUE',
            500
        )

    return make_response(
        "New asset and distribution created successfully",
        200
    )

def update_catalogue(uuid: str, metadata_id: json, data_model: json, access_token_cookies: str, access_token: str) -> Response:
    """
    Update the metadata and data model of an asset in the metadata catalogue.
    """
    logger.debug(f"update_catalogue() - uuid: {uuid}, metadata_id: {metadata_id}")

    response = metadata_catalogue.get_metadata(metadata_id)
    #if response.status_code == 404:
    #    response = metadata_catalogue.create_metadata(metadata_id, data_model)

    jsonld_metadata = response.text

    graph_original = metadata_catalogue.build_graph(jsonld_metadata)

    graph_updateURL = metadata_catalogue.update_accessURL(uuid, graph_original, metadata_id)

    ##TODO: map the datatype to XSD datatypes
    # data_model = [
    # {"name": "Time_Stamp", "datatype": XSD.dateTime},
    # {"name" : "Flight_Number", "datatype": XSD.string},
    # {"name": "Total_Checked_Bags", "datatype": XSD.integer}
    # ]

    graph_updateSchema = metadata_catalogue.update_schema(graph_updateURL, data_model)

    return graph_updateURL
    # return make_response({
    #     "message": "Graph updated",
    #     "status_code" : 200 
    # })

def get_distributions(dataset_id: str) -> list:
    # Fetch dataset distributions from the metadata catalogue
    response = search.search_dataset(dataset_id=dataset_id)

    if response.status_code != 200:
        raise CustomError(
            f'GatewayError: The Metadata Catalogue returned an invalid response ({response.status_code})!',
            'Metadata Catalogue',
            502,
            response.text
        )

    result = response.json().get('result', {})

    if not result.get('distributions') or len(result.get('distributions')) == 0:
        raise CustomError(
            'No distributions found in the dataset!',
            'Metadata Catalogue',
            404
        )

    return result.get('distributions')

def add_distribution(dataset_id: str, from_distribution_id: str, access_url: str, data_model: DataModel, auth_token: str) -> Response:
    """
    Add a distribution to a dataset in the metadata catalogue.
    """

    try:
        distributions = get_distributions(dataset_id)
        logger.debug(f"Existing distributions:\n {json.dumps(distributions, indent=2)}")

        from_distribution = None
        for dist in distributions:
            if dist['id'] == from_distribution_id:
                from_distribution = dist
                break
        dist_title = from_distribution.get('title', {}).get('en', 'Distribution')
        dist_title = f"Semantically Enriched {dist_title}"

        dist_license = from_distribution.get('license', {}).get('resource', '')
        logger.debug(f"Existing distribution title: {dist_title} and license: {dist_license}")
    except Exception as e:
        logger.exception(f"Error fetching existing distributions: {e}")
        raise CustomError(
            'Error fetching existing distributions!',
            'Metadata Catalogue',
            502
        )

    # Create a schema for the distribution
    logger.debug(f"Creating schema for the new distribution ...")
    schema = None
    if data_model.columns:
        schema = [
            CsvwColumn(
                csvw_name=column.name,
                csvw_title=column.name.replace('_', ' '),
                csvw_datatype=column.dataType,
                csvw_format=None,
            ) for column in data_model.columns
        ]

    # Get the current time in UTC and format it
    logger.debug("Creating distribution ...")
    current_time_utc = datetime.now(timezone.utc)
    formatted_time = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    # TODO: get byte size and issued date from the data storage
    distribution = DcatDistribution(
        dcat_title=dist_title,
        dcat_access_url=access_url,
        dct_license=dist_license,
        dct_format='https://publications.europa.eu/resource/authority/file-type/SQL',
        dct_issued=formatted_time,
        dct_type='https://publications.europa.eu/resource/authority/distribution-type/DOWNLOADABLE_FILE',
        dcat_byte_size=None,
        pv_schema=schema,
    )

    logger.debug(f"Posting distribution: {distribution.serialize(rdf_format='turtle')}")
    response = metadata_catalogue.add_distribution(
        dataset_id=dataset_id,
        distribution=distribution,
        auth_token=auth_token,
    )

    if response.status_code != 201 and response.status_code != 200 and response.status_code != 204:
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response text: {response.text}")

        raise CustomError(
            'GatewayError: The Metadata Catalogue returned an invalid response!',
            'Metadata Catalogue',
            502,
            response.text
        )

    return make_response(
        "Distribution created",
        200
    )


def rdf_to_json(filename):
    """
    Converts RDF data from a specified file into a JSON structure containing datatype properties.

    This function loads an RDF graph from the given file and identifies all subjects
    with datatype properties (OWL DatatypeProperty). For each subject, it retrieves
    related datatype URIs under the XML Schema (xsd) namespace. The function then
    structures these properties, including their names and full URIs, into a JSON
    format and prints the result.

    Parameters:
        filename (str): The path to the RDF file to be parsed.

    Returns:
        dict: A dictionary with a "properties" key containing a list of datatype
              properties, each as a dictionary with keys "dataType", "dataTypeURI",
              "name", and "nameURI".
    """

    # Load the RDF graph
    g = Graph()
    g.parse(filename, format="xml")  # Adjust format as needed

    # Define the two URIs
    datatype_property_uri = URIRef("http://www.w3.org/2002/07/owl#DatatypeProperty")
    xsd_base_uri = "http://www.w3.org/2001/XMLSchema#"

    # List to store the properties
    properties_list = []

    # Step 1: Find all subjects where the object is owl:DatatypeProperty
    for subj, pred, obj in g.triples((None, None, datatype_property_uri)):
        # Step 2: For each subject, check if it's connected to a triple where the object has the base URI xsd
        for s2, p2, o2 in g.triples((subj, None, None)):
            # Check if the object starts with the XMLSchema base URI
            if isinstance(o2, URIRef) and str(o2).startswith(xsd_base_uri):
                # Extract the datatype and the subject name
                data_type = str(o2).split("#")[-1]  # Extract the part after # (e.g., string, float, etc.)
                name = str(subj).split("#")[-1]     # Extract the part after # in the subject (e.g., LaserAngularWidth)

                # Append the property as a dictionary with URIs included
                properties_list.append({
                    "dataType": data_type,
                    "dataTypeURI": str(o2),     # Full URI of the datatype
                    "name": name,
                    "nameURI": str(subj)        # Full URI of the subject
                })

    # Structure the output dictionary
    output = {
        "properties": properties_list
    }

    # Print the output in JSON-like format
    print(json.dumps(output, indent=2))

    return output