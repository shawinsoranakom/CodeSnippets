def find_object(expected_object, object_list):
    for obj in object_list:
        if isinstance(obj, list):
            found = find_object(expected_object, obj)
            if found:
                return found

        all_ok = True
        if obj != expected_object:
            if not isinstance(expected_object, dict):
                all_ok = False
            else:
                for k, v in expected_object.items():
                    if not find_recursive(k, v, obj):
                        all_ok = False
                        break
        if all_ok:
            return obj
    return None