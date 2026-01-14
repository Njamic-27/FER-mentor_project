import pyspark
import sedona
import os

import util
from enum import Enum

import sedona.sql.types
from pyspark.sql import SparkSession

from collections import defaultdict

import logging

from pyspark.logger import PySparkLogger
console_logger = PySparkLogger.getLogger("ConsoleLogger")
console_logger.setLevel(logging.INFO)


class MapFormat(Enum):
    PBF = 1
    PARQUET = 2


class LoaderErrror(Exception):
    pass


class Loader:
    def __init__(self, maps_directory: str, spark_session: SparkSession):
        self._maps_directory = maps_directory
        self._spark_session = spark_session

        if not os.path.isdir(maps_directory):
            raise LoaderErrror(f"{maps_directory} is not a directory.")

        self._map_files: dict[str, list[dict]] = defaultdict(list)
        for filename in os.listdir(self._maps_directory):
            extension = util.get_filename_extension(filename)
            map_name = util.get_filename_without_extension(filename)
            full_path=os.path.join(self._maps_directory, filename)

            if extension in (".osm.pbf", ".pbf", ):
                self._map_files[map_name].append(dict(
                    format=MapFormat.PBF,
                    full_path=full_path,
                ))
            elif extension in (".parquet", ):
                self._map_files[map_name].append(dict(
                    format=MapFormat.PARQUET,
                    full_path=full_path,
                ))
            else:
                continue

    def load_map(self, map_name: str, format: MapFormat) -> pyspark.sql.DataFrame:
        if map_name not in self._map_files:
            raise LoaderErrror(f"Map {map_name} not found.")

        maps = self._map_files[map_name]
        if format not in [map_info["format"] for map_info in maps]:
            raise LoaderErrror(f"Map {map_name} not available in format {format.name}.")
        
        maps = self._map_files[map_name]
        for map_info in maps:
            if map_info["format"] == MapFormat.PARQUET:
                df = self._spark_session.read.format("geoparquet").load(map_info["full_path"])
                assert isinstance(df.schema["geometry"].dataType, sedona.sql.types.GeometryType)
                return df
            elif map_info["format"] == MapFormat.PBF:
                return self._spark_session.read.format("osmpbf").load(map_info["full_path"])


class IDontKnowHowToNameThis:
    def __init__(self, spark_session: SparkSession):
        pass

    def parse_ways(df: pyspark.sql.DataFrame):
        from pyspark.sql.functions import col
        from sedona.spark.sql import ST_Point, ST_MakeLine
        from pyspark.sql.functions import sort_array, collect_list, struct, posexplode, size

        df_ways = df.filter(col("kind") == "way")
        df_nodes = df.filter(col("kind") == "node")

        console_logger.info("Ignoring ways with 0 refs.")
        df_ways = df_ways.filter(col("refs").isNotNull() & (size(col("refs")) > 0))

        df_ways = df_ways.limit(10) # TODO: remove limit

        df_ways = df_ways \
            .select(
                "*",
                posexplode("refs").alias("pos", "node_id"),
            ) \
            .alias("ways").join(other=df_nodes.alias("nodes"), on=(col("ways.node_id") == col("nodes.id"))) \
            .groupBy("ways.id", "ways.tags").agg(
                ST_MakeLine(
                    sort_array(
                        collect_list(
                            struct(
                                "pos",
                                ST_Point(col("nodes.location.longitude"), col("nodes.location.latitude")).alias("point"),
                            )
                        )
                    )["point"]
                ).alias("geometry")
            )
        return df_ways
