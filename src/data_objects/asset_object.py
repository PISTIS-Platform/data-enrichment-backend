from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union


class MetaData(BaseModel):
    id : str


# Data type mapping (from API to XSD Namespace)
data_type_mapping = {
    "Integer": "integer",
    "DateTime": "dateTime",
    "String": "string",
    "Float": "float",
    "Double": "double",
    "Boolean": "boolean",
    "Date": "date",
}

class Column(BaseModel):
    name: str
    dataType: str

    @field_validator("dataType", mode="before")
    def normalize_data_type(cls, value):
        return data_type_mapping.get(value, value)

class DataModel(BaseModel):
    columns: List[Column]


class Data(BaseModel):
    rows: List[List[Union[int, float, str]]]


class Asset(BaseModel):
    metadata: Optional[MetaData]
    data_model: Optional[DataModel]
    data: Optional[Data]


