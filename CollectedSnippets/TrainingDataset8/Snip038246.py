def is_snowpark_data_object(obj: object) -> bool:
    """True if obj is of type snowflake.snowpark.dataframe.DataFrame, snowflake.snowpark.table.Table or
    True when obj is a list which contains snowflake.snowpark.row.Row,
    False otherwise"""
    if is_type(obj, _SNOWPARK_TABLE_TYPE_STR):
        return True
    if is_type(obj, _SNOWPARK_DF_TYPE_STR):
        return True
    if not isinstance(obj, list):
        return False
    if len(obj) < 1:
        return False
    if not hasattr(obj[0], "__class__"):
        return False
    return is_type(obj[0], _SNOWPARK_DF_ROW_TYPE_STR)