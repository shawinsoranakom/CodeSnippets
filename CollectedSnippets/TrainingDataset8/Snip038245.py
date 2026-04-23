def is_snowpark_or_pyspark_data_object(obj: object) -> bool:
    """True if if obj is of type snowflake.snowpark.dataframe.DataFrame, snowflake.snowpark.table.Table or
    True when obj is a list which contains snowflake.snowpark.row.Row or True when obj is of type pyspark.sql.dataframe.DataFrame
    False otherwise"""
    return is_snowpark_data_object(obj) or is_pyspark_data_object(obj)