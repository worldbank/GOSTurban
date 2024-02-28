# -*- coding: utf-8 -*-

import os
import time
import pandas as pd
import geopandas as gpd
import h2o
from h2o.automl import H2OAutoML
from h2o.frame import H2OFrame

### Credit: Original code was developed by Alex Chunet and later revised by Eigo Tateishi ###


start_time = time.time()

### Initial file setting --------------------------------------------------------------------
pth = os.getcwd()
building_file = "/Niamey_data/buildings_altered.shp"
sample_file = "/Niamey_data/Niamey_sample_data.shp"

# Read a processed Building Footprint layer
building_df = gpd.read_file(pth + building_file)
building_df = building_df.to_crs({"init": "epsg:4326"})

# Read a Sample Area layer
sample_area = gpd.read_file(pth + sample_file)
sample_area = sample_area.to_crs({"init": "epsg:4326"})

# Urban classes to be used in the sample layer and for classification
# Assign unique integer for each class by yourself here.
class_map = {"middle income": 1, "informal": 2, "formal": 3, "commercial": 4}


### Variable prep here ----------------------------------------------------------------------

# Here, adjust your prediction and response variables. Modify the code below to satisfy your needs.
# Current setting is very basic: Apply all variables in the building_df.
col = building_df.columns
predictors = list(col[1:21])
response = "type"


### Generate a training data by intersecting 'building_df' and 'sample_area'-----------------
# Set urban class default as 'unknown'

source_df = building_df.copy()

source_df["type"] = "unknown"

# Create an empty DF for append
training_data = pd.DataFrame()

# 'training_data' is now our official 'training data' for the ML model.
for index, row in sample_area.iterrows():
    x = row.geometry
    y = row.type

    df_temp = source_df[source_df.intersects(x)].copy()
    df_temp["type"] = y

    training_data = training_data.append(df_temp)

training_data["type"] = training_data["type"].map(class_map)


### Model training here ---------------------------------------------------------------------
h2o.init()

# Convert the training data to an h2o frame.
# NOTE that this process will be inefficien if the original data has many NaNs.
hf = H2OFrame(training_data)


# This block of code is fairly h2o standard. It trains 20 models on this data,
# limiting the runtime to 1 hour. At the end of an hour or training 20 models,
# whichever is first, it returns a DataFrame of predictions as preds, ordered by the quality of their predictions.

# Split 'hf' into a taraining frame and validation frame.
train, valid = hf.split_frame(ratios=[0.8], seed=10)

# Identify predictors and response
x = predictors
y = response

## For binary classification, response should be a factor
train[y] = train[y].asfactor()
valid[y] = valid[y].asfactor()

# Run AutoML for 20 base models (limited to 1 hour max runtime by default)
aml = H2OAutoML(max_models=20, seed=1)
aml.train(x=x, y=y, training_frame=train)

# View the AutoML Leaderboard
lb = aml.leaderboard


# Print all rows instead of default (10 rows)
lb.head(rows=lb.nrows)

print("** Model validation with 'valid' hf **")
preds = aml.leader.predict(valid)

# Here, we print out the performance of our top performing model.
res = aml.leader.model_performance(valid)

print(res)

# We save the model down to its own save location.
model_path = h2o.save_model(model=aml.leader, path=pth, force=True)


### Model fitting here ----------------------------------------------------------------------

# h2o struggled to generate predictions for more than 100,000 rows at a time.
# Thus, we split the original DataFrame into 100,000 row chunks, run the predictions on
# the h2o version of the frame, then send these to file.

max_row_size = 100000

chunk_num = int(len(building_df) / max_row_size)
chunk_mod = len(building_df) % max_row_size

building_df["type"] = "unknown"


def MLpred(df):
    df_input = df[predictors]
    # Extract predictor cols only (specified by the 'predictors' LIST)
    hf_temp = H2OFrame(df_input)

    preds_temp = aml.leader.predict(hf_temp)
    pred_df_temp = preds_temp.as_data_frame()

    # add 'PID' to 'pred_df_temp' so that it will be merged to the original 'df.'
    df.reset_index(inplace=True)
    pred_df_temp["PID"] = df.PID

    ans = pd.merge(df, pred_df_temp, on="PID")

    return ans


# Create an empty DF for append
prediction_df = pd.DataFrame()

for i in range(0, chunk_num):
    if i == 0:
        print("Processing Chunk No. {} ----> row 0–{}".format(i + 1, max_row_size))
        df_temp2 = building_df[0:max_row_size].copy()

        # Prediction process here
        pred_x = MLpred(df_temp2)

        prediction_df = prediction_df.append(pred_x)

    else:
        start = i * max_row_size
        stop = (i * max_row_size) + max_row_size
        print("Processing Chunk No. {} ----> row {}–{}".format(i + 1, start, stop))
        df_temp2 = building_df[start:stop].copy()

        # Prediction process here
        pred_x = MLpred(df_temp2)

        prediction_df = prediction_df.append(pred_x)

if chunk_mod > 0:
    start = chunk_num * max_row_size
    print("Processing Chunk No. {} ----> row {} till the end".format(i + 1, start))
    df_temp2 = building_df[start:].copy()

    # Prediction process here
    pred_x = MLpred(df_temp2)

    prediction_df = prediction_df.append(pred_x)


### Exporting -------------------------------------------
print("Exporting reulst to shapefile...")
output_path = pth + "\prediction_result.shp"
prediction_df.to_file(output_path, driver="ESRI Shapefile")


### Refreshing H2O cluster (if necessary) -------------------------------------------

elapsed_time = (time.time() - start_time) / 60
print("elapsed_time:{0}".format(elapsed_time) + "[Min]")

h2o.cluster().shutdown(prompt=True)
