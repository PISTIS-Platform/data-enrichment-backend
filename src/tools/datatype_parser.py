from datetime import datetime
import re
import numpy as np
import pandas as pd

date_formats_allowed = {
            'dateTime':[
                '%Y-%m-%dT%H:%M:%f %Z',
                '%Y.%m.%dT%H:%M:%f %Z',
                '%Y/%m/%dT%H:%M:%f %Z',
                
                '%Y-%m-%dT%H:%M %Z',
                '%Y.%m.%dT%H:%M %Z',
                '%Y/%m/%dT%H:%M %Z',

                '%Y-%m-%dT%H:%M:%f%Z',
                '%Y.%m.%dT%H:%M:%f%Z',
                '%Y/%m/%dT%H:%M:%f%Z',
                
                '%Y-%m-%dT%H:%M%Z',
                '%Y.%m.%dT%H:%M%Z',
                '%Y/%m/%dT%H:%M%Z',
                
                
                '%Y-%m-%dT%H:%M:%f',
                '%Y.%m.%dT%H:%M:%f',
                '%Y/%m/%dT%H:%M:%f',
                
                '%Y-%m-%dT%H:%M',
                '%Y.%m.%dT%H:%M',
                '%Y/%m/%dT%H:%M',
                
                
                '%Y-%m-%dT%H:%M:%f %z',
                '%Y.%m.%dT%H:%M:%f %z',
                '%Y/%m/%dT%H:%M:%f %z',
                
                '%Y-%m-%dT%H:%M %z',
                '%Y.%m.%dT%H:%M %z',
                '%Y/%m/%dT%H:%M %z',

                '%Y-%m-%dT%H:%M:%f%z',
                '%Y.%m.%dT%H:%M:%f%z',
                '%Y/%m/%dT%H:%M:%f%z',
                
                '%Y-%m-%dT%H:%M%z',
                '%Y.%m.%dT%H:%M%z',
                '%Y/%m/%dT%H:%M%z',
                
                '%Y-%m-%dT%H:%M:%f',
                '%Y.%m.%dT%H:%M:%f',
                '%Y/%m/%dT%H:%M:%f',
                
                '%Y-%m-%dT%H:%M',
                '%Y.%m.%dT%H:%M',
                '%Y/%m/%dT%H:%M',
                
                
                '%a, %d %b %Y %H:%M:%f %Z',
                '%a, %d %b %Y %H:%M %Z',
                
                '%a, %d %b %Y %H:%M:%f %z',
                '%a, %d %b %Y %H:%M %z',
                
                '%a, %d %b %Y %H:%M:%f%Z',
                '%a, %d %b %Y %H:%M%Z',
                
                '%a, %d %b %Y %H:%M:%f%z',
                '%a, %d %b %Y %H:%M%z',

                '%a, %d %b %Y %H:%M:%f',
                '%a, %d %b %Y %H:%M',
                
                
                '%Y-%m-%d %H:%M:%f %Z',
                '%Y/%m/%d %H:%M:%f %Z',
                '%Y.%m.%d %H:%M:%f %Z',
                
                '%Y-%m-%d %H:%M %Z',
                '%Y/%m/%d %H:%M %Z',
                '%Y.%m.%d %H:%M %Z',
                
                '%Y-%m-%d %H:%M:%f %z',
                '%Y/%m/%d %H:%M:%f %z',
                '%Y.%m.%d %H:%M:%f %z',
                
                '%Y-%m-%d %H:%M %z',
                '%Y/%m/%d %H:%M %z',
                '%Y.%m.%d %H:%M %z',

                '%Y-%m-%d %H:%M:%f%Z',
                '%Y/%m/%d %H:%M:%f%Z',
                '%Y.%m.%d %H:%M:%f%Z',
                
                '%Y-%m-%d %H:%M%Z',
                '%Y/%m/%d %H:%M%Z',
                '%Y.%m.%d %H:%M%Z',
                
                '%Y-%m-%d %H:%M:%f%z',
                '%Y/%m/%d %H:%M:%f%z',
                '%Y.%m.%d %H:%M:%f%z',
                
                '%Y-%m-%d %H:%M%z',
                '%Y/%m/%d %H:%M%z',
                '%Y.%m.%d %H:%M%z',
                
                '%Y-%m-%d %H:%M:%f',
                '%Y/%m/%d %H:%M:%f',
                '%Y.%m.%d %H:%M:%f',
                
                '%Y-%m-%d %H:%M',
                '%Y/%m/%d %H:%M',
                '%Y.%m.%d %H:%M',

                      ],
            
            'date':[
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y.%m.%d',
                '%a, %d %b'
            ]
}

date_formats_forbidden = {
    '%d.%m.%Y': ('%Y.%m.%d', 'date')
}
    
    


def parse_datatype(entry) -> str:
    s = str(entry)
    for type_, formats in date_formats_allowed.items():
        for format_ in formats:
            try:
                datetime.strptime(s, format_)
                return type_
            except ValueError:
                pass
    for format_forbidden in list(date_formats_forbidden.keys()):
        try:
            datetime.strptime(s, format_forbidden)
            return format_forbidden
        except ValueError:
            pass
    regex = re.compile(r'(?P<integer>^[+-]?[1-2][1-9][1-9][1-9][1-9][1-9][1-9][1-9][1-9][1-7]$|^[+-]?\d{1,9}$)|(?P<bigint>^[+-]?\d+$)|(?P<double>^[+-]?\d{1,2}e[-][0]?[0]?[7-9]$|^[+-]?\d{1,2}e[-][1][0-5]$|^[+-]?\d{1,2}e[+]?\d+$|^[+-]?\d*\.\d{7,15}$|^[+-]?\d{1,2}\.\d{1,15}e[+]?\d+$|^[+-]?\d{1,2}\.\d{1,5}e[-][0]?[0]?[1-9]$|^[+-]?\d{1,2}\.\d{1,5}e[-][0]?10$)|(?P<float>^[+-]?\d*\.\d{1,6}$|^[+-]?\d{1,2}e[-][1-6]$)|(?P<string>)')
    return r"%s" % regex.search(s).lastgroup




def convert_date(date, origin_format, desired_format):
    return datetime.strptime(date, origin_format).strftime(desired_format)



"""
def convert_dates(csvList, dtypes) -> (list, list):
    for column in dtypes:
        if column['dataType'] in list(date_formats_forbidden.keys()):
            index = np.where(csvList[0] == column['name'])[0][0]
            csvList[1::,index] = np.array(list(map(lambda x: convert_date(x, column['dataType'], date_formats_forbidden[column['dataType']][0]), csvList[1::,index])))
            column['dataType'] = date_formats_forbidden[column['dataType']][1]
    return csvList.tolist(), dtypes

"""

def convert_dates(df, dtypes) -> (pd.DataFrame, list):
    for column in dtypes:
        if column['dataType'] in date_formats_forbidden:
            col_name = column['name']
            forbidden_format = column['dataType']
            desired_format, new_dataType = date_formats_forbidden[forbidden_format]

            # Apply the conversion to the column, handling missing values
            df[col_name] = df[col_name].apply(
                lambda x: convert_date(x, forbidden_format, desired_format)
                if pd.notnull(x) else x
            )

            # Update the data type in the dtypes list
            column['dataType'] = new_dataType
    return df, dtypes