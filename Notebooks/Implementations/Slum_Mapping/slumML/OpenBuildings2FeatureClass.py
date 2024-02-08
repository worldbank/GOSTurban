# -*- coding: utf-8 -*-
"""
OpenBuildings2FeatureClass
To convert the CSV file(s) of Google Open Buildings to a Feature Class.
Coded by Eigo Tateishi (GOST, World Bank @ Washington D.C.)
V 2021 Oct 19.
"""

import arcpy
import pandas as pd


### Set the workplace and read data here---------------------------------------------

data = 'Cairo_metropolitan_area.csv'#Target Google OpenBuilding CSV file. Alter the path if necessary.
gdb = 'D:/GoogleBuildings.gdb'#Geodatabase to store the transformed data.
fc_name = 'Cairo_metropolitan_area_TEST'#The name to be used for the new feature class.
arcpy.env.workspace = gdb#ArcGIS Pro workplace setting. Keep it as it is unless you need any specific adjustment.
spRef = arcpy.SpatialReference(4326)#Specify the spatial reference for the process. For OpenBuilding, EPSG:4326
tarConf = 0.5#Confidence threshold, if necessary. If you want all records, insert 0.0.

with open(data, 'r', encoding="utf-8_sig", ) as F:
    df = pd.read_csv(F, sep=",")



###----------------------------------------------------------------------------------
### Specify a target field list for the InsertCursor function below.
### This list should be exactly same as 'fields_desc' below except for 'SHAPE@' token.
fields = [
          'latitude',
          'longitude',
          'areaSize_m2',
          'confidence',
          'fullPlus_code',
          'SHAPE@'
          ]


### Create a new empty feature class here--------------------------------------------

# Set fields definition to be created within an empty feature class:
fields_desc = [
          ['latitude', 'Double'],
          ['longitude', 'Double'],
          ['areaSize_m2', 'Double'],
          ['confidence', 'Double'],
          ['fullPlus_code', 'Text']
          ]

arcpy.management.CreateFeatureclass(gdb, fc_name, "Polygon", "", "", "", spRef)
arcpy.management.AddFields(fc_name, fields_desc)



### Cleaning the raw table and mask by target confidence level-----------------------
df_clean = df[df['geometry'].str.contains('|'.join(['POLYGON']))].copy()
# Select records with a valid geometry (that starts with 'POLYGON').
# If a record starts with invalid texts (such as 'EMPTY'), the record will be removed.

df_conf = df_clean[df_clean['confidence'] > tarConf].copy()
# Mask the table by confidence level.

### TO TEST THE CODE with a small chunk of data:
#df_test = df_conf.iloc[0:100, :].copy()
#df_test.reset_index(inplace=True, drop=True)



### Main loop - Convert the CSV data to a feature class:-----------------------------
for i, r in df_conf.iterrows():
    
    geomet = arcpy.FromWKT(r['geometry'], spRef)
    lat = r[0]
    long = r[1]
    area = r[2]
    conf = r[3]
    plus = r[5]
    
    rowList = [lat, long, area, conf, plus, geomet]
    
    with arcpy.da.InsertCursor(fc_name, fields) as cursor:
        cursor.insertRow(rowList)


print('END PROCESS.')