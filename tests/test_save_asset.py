from config import *

class TestSaveAsset(unittest.TestCase):
    endpoint = DATA_ENRICHMENT_URL + "/save_asset"

    def test_save_asset(self):
        header = {
            'Content-Type': 'application/json',
            'Authorization': BEARER_TOKEN
        }

        body = """
        {
            "metadata": {
                "id" : "804596e9-3588-4989-a57c-3c91424936c8"
            },
            "data_model": {
                "columns": [
                    {
                        "dataType": "Integer",
                        "name": "ProductID"
                    },
                    {
                        "dataType": "Integer",
                        "name": "ScheduledQuantity"
                    },
                    {
                        "dataType": "String",
                        "name": "SaleStatus"
                    },
                    {
                        "dataType": "DateTime",
                        "name": "ScheduledDate"
                    }
                ]
            }
        }
        """


