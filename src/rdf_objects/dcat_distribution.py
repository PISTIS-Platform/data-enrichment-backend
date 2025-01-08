from attr import dataclass
from rdflib import Namespace, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, XSD
from typing import List, Optional, Union


DCAT = Namespace('http://www.w3.org/ns/dcat#')
DCT = Namespace('http://purl.org/dc/terms/')
PV = Namespace("https://piveau.eu/ns/voc#")
CSVW = Namespace('http://www.w3.org/ns/csvw#')
NS4 = Namespace("https://piveau.eu/ns/")


@dataclass
class CsvwColumn:
    """
    A class to represent a CSVW column of a Distribution schema.
    """
    csvw_name: str
    csvw_title: str
    csvw_datatype: str
    csvw_format: Optional[str] = None


@dataclass
class DcatDistribution:
    """
    A class to represent a DCAT Distribution.
    """
    dcat_title: str
    dcat_access_url: str
    dct_format: str
    dct_issued: str
    dct_type: str
    dct_license: Optional[str] = None
    dcat_byte_size: Optional[int] = None
    pv_schema: Optional[List[CsvwColumn]] = None

    def serialize(self, rdf_format: str = None):
        """
        Serialize a DCAT Distribution as RDF.
        :param rdf_format: The RDF serialization format to use, e.g. 'turtle', 'xml', etc. (optional)
        :return: The serialized RDF graph as a string if rdf_format is given, otherwise the graph itself.
        """
        g = Graph()

        g.bind("pv", PV)

        # Subject URI for the distribution
        dist_uri = URIRef('https://www.pistis-project.eu/set/new_distribution')

        # Add distribution properties
        g.add((dist_uri, RDF.type, DCAT.Distribution))
        g.add((dist_uri, DCT.title, Literal(self.dcat_title)))
        g.add((dist_uri, DCAT.accessURL, URIRef(self.dcat_access_url)))
        g.add((dist_uri, DCT['format'], URIRef(self.dct_format)))
        g.add((dist_uri, DCT.issued, Literal(self.dct_issued, datatype=XSD.dateTime)))
        g.add((dist_uri, DCT.type, URIRef(self.dct_type)))
        if self.dct_license:
            g.add((dist_uri, DCT.license, URIRef(self.dct_license)))
        if self.dcat_byte_size:
            g.add((dist_uri, DCAT.byteSize, Literal(self.dcat_byte_size, datatype=XSD.decimal)))

        # Add the data schema if it exists
        if self.pv_schema:
            schema_bnode = BNode()
            g.add((dist_uri, PV.schema, schema_bnode))
            g.add((schema_bnode, RDF.type, PV.CSVSchema))

            table_schema_bnode = BNode()
            g.add((schema_bnode, CSVW.tableSchema, table_schema_bnode))
            g.add((table_schema_bnode, RDF.type, CSVW.Schema))

            for column in self.pv_schema:
                column_bnode = BNode()

                g.add((column_bnode, CSVW.name, Literal(column.csvw_name)))
                g.add((column_bnode, CSVW.title, Literal(column.csvw_title)))
                g.add((column_bnode, CSVW.datatype, URIRef(XSD[column.csvw_datatype])))

                if column.csvw_format:
                    g.add((column_bnode, CSVW["format"], Literal(column.csvw_format)))

                g.add((table_schema_bnode, CSVW.column, column_bnode))

        if rdf_format:
            return g.serialize(format=rdf_format)
        else:
            return g