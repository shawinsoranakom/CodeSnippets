def create_pyspark_dataframe_with_mocked_map_data() -> PySparkDataFrame:
    """Returns PySpark DataFrame with mocked map data."""
    spark = SparkSession.builder.appName("snowflake.com").getOrCreate()
    map_schema = StructType(
        [StructField("lat", FloatType(), True), StructField("lon", FloatType(), True)]
    )
    return spark.createDataFrame(data=MAP_DATA, schema=map_schema)