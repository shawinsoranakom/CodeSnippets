def get_query_list_default(device_ids: list[int] = Query(default=[])) -> list[int]:
    return device_ids