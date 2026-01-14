import os
import logging

from pyspark.logger import PySparkLogger

import sys
sys.path.append("/docker-shared-data/bench")
import loader

# Create a logger that logs to console
console_logger = PySparkLogger.getLogger("ConsoleLogger")
console_logger.setLevel(logging.INFO)

MAPS_DIR = "/docker-shared-data/openstreetmap/maps/processed"
MAP_NAME = "croatia-260106"


import pyspark.sql
import sedona.spark

spark = pyspark.sql.SparkSession.builder \
    .master("local[4]") \
    .appName("Learning Sedona") \
    .getOrCreate()

spark_session = sedona.spark.SedonaContext.create(spark=spark)

map_loader = loader.Loader(maps_directory=MAPS_DIR, spark_session=spark_session)
df = map_loader.load_map(MAP_NAME, loader.MapFormat.PARQUET)

df.show(10, truncate=False)

df = loader.parse(df)

df.show(10, truncate=False)

# df.write.format("geoparquet").save(DEST_DATA_DIR + f"/{MAP_NAME}.parquet")