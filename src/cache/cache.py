import sqlite3
import json
import sys
from dataclasses import dataclass
from data_objects.asset_object import *

@dataclass(frozen=True)
class Cache():

    def __init__(self, name):
        object.__setattr__(self, '_name', name)
        conn = sqlite3.connect(self._name, check_same_thread=False)
        object.__setattr__(self, '_conn', conn)
        cur = self._conn.cursor()
        command = 'CREATE TABLE IF NOT EXISTS asset (uuid TEXT UNIQUE, data TEXT, from_file INTEGER);'
        cur.execute(command)
        command = 'CREATE TABLE IF NOT EXISTS datamodel (properties TEXT);'
        cur.execute(command)
        cur.close()

    
    def store_asset(self, asset:Asset, uuid:str, from_file:bool):
        cur = self._conn.cursor()
        asset_string = asset.model_dump_json()
        command = 'INSERT OR REPLACE INTO asset (uuid, data, from_file) VALUES (\'{}\', \'{}\', \'{}\');'.format(uuid, asset_string, int(from_file))
        # print("\n\n: INSERT: ", command, file=sys.stderr)
        cur.execute(command)
        cur.close()

    

    def get_asset(self, uuid:str) -> (Asset, str):
        """
        Returns the asset with the given uuid from the cache database.

        """
        command = 'SELECT data, from_file FROM asset WHERE uuid = (\'{}\');'.format(uuid)
        conn = sqlite3.connect(self._name)
        cur = self._conn.cursor()
        cur.execute(command)
        result = cur.fetchall()
        data = result[0][0]
        from_file = result[0][1]
        asset = Asset.model_validate_json(data.replace('\'', '"'))
        cur.close()

        return asset, from_file



    def get_properties(self) -> list:
        command = 'SELECT properties FROM datamodel;'
        conn = sqlite3.connect(self._name)
        cur = self._conn.cursor()
        cur.execute(command)
        data = cur.fetchall()[0][0]
        properties = json.loads(data.replace('\'', '"'))['properties']
        cur.close()

        return properties
    

    def update_kgm_properties(self, properties:dict):
        command = 'DELETE FROM datamodel'
        conn = sqlite3.connect(self._name)
        cur = self._conn.cursor()
        cur.execute(command)
        properties_string = json.dumps(properties)
        command = 'INSERT INTO datamodel (properties) VALUES (\'{}\');'.format(properties_string)
        cur.execute(command)
        cur.close()

    
    def clear_kgm_properties(self):
        command = 'DELETE FROM datamodel'
        conn = sqlite3.connect(self._name)
        cur = self._conn.cursor()
        cur.execute(command)
        cur.close()

    
    def delete_asset(self, uuid:str):
        conn = sqlite3.connect(self._name)
        cur = self._conn.cursor()
        command = 'DELETE FROM asset WHERE uuid = \'{}\';'.format(uuid)
        cur.execute(command)
        cur.close()
    

