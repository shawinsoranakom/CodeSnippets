def get_return_data_type(func_name):
    """Return a somewhat-helpful data type given a function name"""
    if func_name.startswith("get_"):
        if func_name.endswith("_list"):
            return "List"
        elif func_name.endswith("_count"):
            return "Integer"
    return ""