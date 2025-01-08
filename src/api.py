from flask import Flask, jsonify, request, make_response, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from logging.config import dictConfig
from flask_restx import Api
import json
from functools import wraps
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config
import os
from data_objects.asset_object import *
from data_layer import *
from logic_layer import*
from util import get_logger
from tools.identity_manager import *
from tools.error_handler import *
from flask_cors import CORS, cross_origin
from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import DCTERMS, DCAT, RDF, XSD


# identity_manager = IdentityManager(os.getenv('IDENTITY_MANAGER', 'https://iam-backend.ai4manufacturing.eu/api/v1/auth'))

app = Flask(__name__)
app.config.from_object(Config)
app.debug = True
CORS(app, supports_credentials=True)
app.config['CORS_SUPPORTS_CREDENTIALS'] = True

# SWAGGER_URL = ''
# API_URL = '/static/swagger.json'
SWAGGER_URL = '/srv/data-enrichment-backend'
API_URL = '/srv/data-enrichment-backend/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PISTIS Data Enrichment"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix='/')

logger = get_logger("api")
### API KEY specification
# def token_required(f):
#     '''decorator function to check tokens in header'''
#     @wraps(f)
#     def wrapped(*args, **kwargs):
#         api_key = request.headers.get("Authorization")
#         if api_key == "7KbyV3DZfPQq2rJ8XgtNpWVQp5ZdA9mG":
#             return f(*args,**kwargs)
#         else:                 
#             return make_response (jsonify({'message': 'API Key is wrong, authentication failed'}), 401)
#     return wrapped

def token_required(f):
    '''decorator function to check tokens in header'''
    @wraps(f)
    def wrapped(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token == "7KbyV3DZfPQq2rJ8XgtNpWVQp5ZdA9mG":      
            return f(*args,**kwargs)
        if token and token.startswith('Bearer '):
            # print("its a bearer token", flush=True)
            identity_object = IdentityManager('application/x-www-form-urlencoded', 'urn:ietf:params:oauth:grant-type:uma-ticket', '')
            response = IdentityManagerApi().user_account_authorize(identity_object,token.split(' ')[1])
            if response.status_code != 200:
                return make_response (jsonify({'message': 'Unauthorized access.'}), 401)
        else:             
            return make_response (jsonify({'message': 'API Key or token is missing, authentication failed'}), 401)
        
        return f(*args,**kwargs)
    return wrapped

@app.errorhandler(CustomError)
def handleError(e):
        return make_response(
            jsonify(e.__dict__),
            e.status_code
        )



# @app.route('/update_datamodel', methods=['POST'])
# @token_required
# def update_datamodel():
#     access_token_cookies = request.cookies.get('access_token')
#     access_token_headers = request.headers.get('Authorization')

#     identity_manager.authorize(access_token_cookies=access_token_cookies, access_token_headers=access_token_headers)
#     my_response = update_kgm_properties(access_token_cookies=access_token_cookies, access_token_headers=access_token_headers)

#     return make_response(
#         jsonify(my_response.json()),
#         my_response.status_code
#         )

@app.route('/livesearch_data_model', methods=['POST', 'GET'])
@token_required
def livesearch_data_model():
    # access_token_cookies = request.cookies.get('access_token')
    # access_token_headers = request.headers.get('Authorization')

    # identity_manager.authorize(access_token_cookies=access_token_cookies, access_token_headers=access_token_headers)

    try:
        sequence = request.json['sequence']
        search_results = livesearch(sequence=sequence, access_token_cookies=None, access_token_headers=None)

        return make_response(
            jsonify(search_results),
            200
            )

    except KeyError:
        raise CustomError(
            'Argument "sequence" not provided (correctly) in the request!',
            'FILE DATA HARVESTER BACKEND',
            400
            )
    

@app.route('/get_asset', methods=['GET'])
@token_required
def get_asset():
    """
    Receives a request from the data enrichment frontend containing:
    - the dataset id (id of the dataset in the catalog)
    - the distribution id (id of the distribution in the metadata catalog)
    - the file type (e.g. 'csv', 'json', 'xml', etc.)

    The function then retrieves the asset from the data storage and caches it so it can be used for data enrichment.
    """
    # Create header dictionary if Authorization header is present
    auth_token = request.headers.get("Authorization")

    if (dataset_id := request.args.get('dataset_id')) is None:
        return make_response(
            "Failed to retrieve Asset, dataset_id not provided",
            400
        )

    if (distribution_id := request.args.get('distribution_id')) is None:
        return make_response(
            "Failed to retrieve Asset, distribution_id not provided",
            400
        )

    if (file_type := request.args.get('file_type')) is None:
        return make_response(
            "Failed to retrieve Asset, file_type not provided",
            400
        )

    try:
        my_response = retrieve_file(
            dataset_id=dataset_id,
            distribution_id=distribution_id,
            file_type=file_type,
            access_token_cookies=None,
            auth_token=auth_token
        )
        print(f"Api.py - my_response: {my_response.json()}", flush=True)
    except Exception as e:
        logger.error(f"Error retrieving asset: {e}")
        return make_response("Failed to retrieve Asset", 500)

    return make_response(
        jsonify(my_response.json()),
        my_response.status_code
    )



##TODO: Take the id returned by the update_asset
@app.route('/save_asset', methods=['POST'])
@token_required
def save_asset():
    """
    Receives a request from the data enrichment frontend containing:
    - the dataset id (id of the dataset in the catalog)
    - the distribution id (id of the distribution in the metadata catalog)

    The function then fetches the file data using the asset UUID and parses it, creates a new table in the data storage
    with the parsed data and the provided columns, updates the metadata object in the catalogue with the new data model
    and adds a new distribution to the metadata object with the access URL of the new asset in the data storage.
    """

    # TODO: DCAT schema not added correctly
    # TODO: 500 error even though it succeeds
    if (dataset_id := request.args.get('dataset_id')) is None:
        raise CustomError(
            message='Missing dataset_id in the request!',
            origin='DATA ENRICHMENT BACKEND',
            status_code=400
        )

    if (distribution_id := request.args.get('distribution_id')) is None:
        raise CustomError(
            message='Missing distribution_id in the request!',
            origin='DATA ENRICHMENT BACKEND',
            status_code=400
        )

    if (metadata := request.json.get('metadata', None)) is None:
        raise CustomError(
            message='Missing metadata in the request!',
            origin='DATA ENRICHMENT BACKEND',
            status_code=400
        )

    if (data_model := request.json.get('data_model', None)) is None:
        raise CustomError(
            message='Missing data model in the request!',
            origin='DATA ENRICHMENT BACKEND',
            status_code=400
        )

    access_token = request.headers.get("Authorization")

    logger.info(f"Received request /save_asset dataset_id={dataset_id}, distribution_id={distribution_id}")

    # Parse the file data, save the file data as a table in the data storage. Create a new distribution in the catalog.
    # Non-200 status codes are handled within the update_asset function and will raise an error
    try:
        metadata_object = MetaData.model_validate(metadata)
        data_model_object = DataModel.model_validate(data_model)

        # This response includes the dataset id
        create_asset(
            dataset_id=dataset_id,
            distribution_id=distribution_id,
            metadata=metadata_object,
            data_model=data_model_object,
            access_token_cookies=None,
            access_token=access_token
        )

    except Exception as e:
        logger.error(e)
        cache.delete_asset(distribution_id)
        raise CustomError(
            message='Failed to create new Asset',
            origin='DATA ENRICHMENT BACKEND',
            status_code=500
        )

    logger.debug(f"Asset with UUID: {distribution_id} created successfully in the data storage. "
                 f"Deleting asset from cache.")
    cache.delete_asset(distribution_id)
    return make_response(
        "Asset saved successfully",
        200
    )





@app.route('/test', methods=['GET'])
def test():

    # datasetId = 'fbaf79c2-099b-4de3-a59a-50dafadba804'
    datasetId = request.args.get('id')
    print(datasetId, flush=True)
    # namespaces = [
    #     {
    #         'prefix' : 'pv',
    #         'uri' : 'https://piveau.eu/ns/voc'
    #     },
    #     {
    #         'prefix' : 'csvw',
    #         'uri' : 'http://www.w3.org/ns/csvw'
    #     },
    #             {
    #         'prefix' : 'dcat',
    #         'uri' : 'http://www.w3.org/ns/dcat'
    #     }
    # ]


    try:
        response = requests.get(f'https://develop.pistis-market.eu/srv/repo/datasets/{datasetId}')
        jsonld_data = response.text

        g = Graph()
        g.parse(data=jsonld_data, format='json-ld')
        # print(jsonld_data, flush=True)

        # Print the RDF graph in Turtle format (you can choose other formats like 'xml', 'nt', 'n3', etc.)
        # print(g.serialize(format='turtle'), flush=True)
        
        access_url = DCAT.accessURL
        subject_uri = URIRef("https://develop.pistis-market.eu/catset/distribution/8fc2ae6f-01e6-42c6-894a-01021eeb767b")
        new_access_url = URIRef("https://test-url.example.com")

        PV = Namespace("https://piveau.eu/ns/voc")
        CSVW = Namespace("http://www.w3.org/ns/csvw")

        print("NEW GRAPH-------------------------------------------------------------- \n\n", flush=True)

        csv_schema_node = BNode()
        g.add((csv_schema_node, RDF.type, PV.CSVSchema))

        table_schema_node = BNode()
        g.add((csv_schema_node, CSVW.tableSchema, table_schema_node))
        g.add((table_schema_node, RDF.type, CSVW.Schema))

        data_model = [
            {"name": "Time_Stamp", "datatype": XSD.dateTime},
            {"name" : "Flight_Number", "datatype": XSD.string},
            {"name": "Total_Checked_Bags", "datatype": XSD.integer}
        ]

        for column in data_model:
            column_node = BNode()
            g.add((table_schema_node, CSVW.column, column_node))
            g.add((column_node, CSVW.name, Literal(column["name"])))
            g.add((column_node, CSVW.datatype, URIRef(column["datatype"])))

        # Flag to check if any triple was found and modified
        found = False

        # Iterate through the graph to find subjects with an accessURL
        for s, p, o in g.triples((None, access_url, None)):
            if p == access_url:
                # Remove the old triple
                g.remove((s, p, o))
                # Add the new triple with the updated accessURL
                g.add((s, p, new_access_url))
                g.add((s, PV.schema, csv_schema_node))
                found = True
                print(f"Updated accessURL for subject {s} to {new_access_url}")

        # g.add((subject_uri, access_url, new_access_url))
        print(g.serialize(format='turtle'), flush=True)

        print("JSON-LD GRAPH-------------------------------------------------------------- \n\n", flush=True)
        print(g.serialize(format='json-ld'), flush=True)


        return make_response(g.serialize(format='json-ld'),
            response.status_code
            )

    except KeyError:
        raise CustomError(
        'Test failed!',
        'DATA ENRICHMENT BACKEND',
        400
        )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)