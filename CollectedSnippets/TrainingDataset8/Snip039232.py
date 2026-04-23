def create_pyspark_dataframe_with_mocked_personal_data() -> PySparkDataFrame:
    """Returns PySpark DataFrame with mocked personal data."""
    spark = SparkSession.builder.appName("snowflake.com").getOrCreate()
    schema = StructType(
        [
            StructField("firstname", StringType(), True),
            StructField("middlename", StringType(), True),
            StructField("lastname", StringType(), True),
            StructField("id", StringType(), True),
            StructField("gender", StringType(), True),
            StructField("salary", IntegerType(), True),
        ]
    )
    return spark.createDataFrame(data=PERSONAL_DATA, schema=schema)