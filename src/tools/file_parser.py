import csv
import json
from tools.datatype_parser import *
from data_objects.asset_object import *
from detect_delimiter import detect
from io import StringIO
import pandas as pd
from util import get_logger

logger = get_logger('file_parser')

def csvAndTxtToAsset(text: str) -> (Asset, Asset):
    # print("*** Inside csvAndTxtToAsset", flush=True)
    # print("TEXT: " + text, flush=True)

    # Split text into rows and detect delimiter
    text_split = text.splitlines()
    delimiter = detect(text_split[0])
    # print("\n\n***************")
    logger.debug(f"Detected delimiter: {delimiter}")

    # Using csv.reader to handle parsing more robustly
    reader = csv.reader(StringIO(text), delimiter=delimiter)
    
    # Extract rows and determine header length
    logger.debug("Processing header ...")
    rows = list(reader)
    header_length = len(rows[0])

    # Ensure all rows have consistent length by padding with None
    logger.debug("Padding rows ...")
    padded_rows = [
        row + [None] * (header_length - len(row))  # Pad with None for missing columns
        for row in rows if len(row) > 1  # Include rows with more than 1 column
    ]
    # print("\n\n***************")
    # print(f"Padded rows: {padded_rows}", flush=True)

    # Convert padded_rows to a 2D NumPy array with dtype=object
    list_ = np.array(padded_rows, dtype=object)
    # print("\n\n***************")
    # print(f"list_ as 2D numpy array: {list_}", flush=True)

    # Generate dtypes for columns based on the first row
    logger.debug("Generating data types ...")
    logger.debug(f"List: {list_}")
    dtypes = [{'name': column, 'dataType': parse_datatype(list_[1][index])} for index, column in enumerate(list_[0])]
    logger.debug(f"Data model: {dtypes}")

    # Apply date conversion logic if needed
    logger.debug("Converting dates ...")
    list_, dtypes = convert_dates(list_, dtypes)
    # print("\n\n***************")
    # print("list_ after converting dates: ", list_, flush=True)

    # Separate rows and rows preview for data serialization
    logger.debug("Serializing data ...")
    data_rows = list_[1:]
    rows_preview = data_rows[:20]

    # Serialize data and create Asset instances
    data = Data(**{'rows': data_rows})
    data_preview = Data(**{'rows': rows_preview})
    data_model = DataModel(**{'columns': dtypes})

    asset = Asset(
        metadata=None,
        data_model=data_model,
        data=data
    )

    asset_preview = Asset(
        metadata=None,
        data_model=data_model,
        data=data_preview
    )

    return asset, asset_preview


def optimizedCsvAndTxtToAsset(text: str) -> (Asset, Asset):
    logger.debug("Parsing CSV/Text file ...")
    logger.debug(f"Text: {text}")
    first_line = text.partition('\n')[0]  # Faster for large documents
    logger.debug(f"First line: {first_line}")

    delimiter = detect(first_line)
    logger.debug(f"Detected delimiter: {delimiter}")

    # Create DataFrame
    df = pd.read_csv(
        pd.io.common.StringIO(text),
        sep=delimiter,
        dtype=str,
        skipinitialspace=True,
        engine='c',
    )

    df = df.fillna("0")

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')

    json_data = df.to_dict(orient='records')
    logger.debug("DataFrame JSON:\n%s", json.dumps(json_data, indent=4))
    # Remove unwanted characters and whitespace at the end of rows
    # df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    # for col in df.columns:
    #    df[col] = df[col].str.strip()

    # Infer data types and convert dates
    # TODO: This will infer incorrect types if the first row contains missing values
    # TODO: This will also fail to infer boolean types
    dtypes = [{'name': column, 'dataType': parse_datatype(df[column].iloc[0])} for column in df.columns]
    logger.debug(f"Data model: {dtypes}")

    df, dtypes = convert_dates(df, dtypes)

    logger.debug(F"Data rows: {df.values.tolist()}")
    # Create Asset
    data_model = DataModel(**{'columns': dtypes})

    rows = df.values.tolist()
    data = Data(**{'rows': rows})
    data_preview = Data(**{'rows': rows[:20]})

    asset_preview = Asset(
        metadata=None,
        data_model=data_model,
        data=data_preview
    )

    asset = Asset(
        metadata=None,
        data_model=data_model,
        data=data
    )

    logger.debug("==============================")
    logger.debug(data_preview)
    logger.debug("==============================")

    return asset, asset_preview


# Convert xls files to csv
def excelToCSV(excelBytes:bytes) -> str:
    df = pd.read_excel(excelBytes)
    # Selecting and removing empty and unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Apply the decimal comma to dot conversion
    df = convert_decimal_comma_to_dot(df)

    return df.to_csv(index=False)

def jsonToCSV(jsonBytes: bytes) -> str:
    # Decode JSON bytes to a string, then load as JSON
    json_data = json.loads(jsonBytes.decode('utf-8'))

    # Convert the JSON to a DataFrame
    df = pd.DataFrame(json_data)

    # Apply the decimal comma to dot conversion
    df = convert_decimal_comma_to_dot(df)

    # Return CSV format as a string, without the index
    return df.to_csv(index=False)

# Helper function to convert decimal commas to dots in numeric fields
def convert_decimal_comma_to_dot(df: pd.DataFrame) -> pd.DataFrame:
    return df.applymap(lambda x: x.replace(',', '.') if isinstance(x, str) and re.match(r'^\d+,\d+$', x) else x)