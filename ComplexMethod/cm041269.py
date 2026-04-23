def find_recursive(key, value, obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and v == value:
                return True
            if find_recursive(key, value, v):
                return True
    elif isinstance(obj, list):
        for o in obj:
            if find_recursive(key, value, o):
                return True
    else:
        return False