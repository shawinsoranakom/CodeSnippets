def convert(obj):
    if isinstance(obj, str):
        return {"type": "string", "value": obj}
    elif isinstance(obj, bool):
        return {"type": "bool", "value": str(obj).lower()}
    elif isinstance(obj, int):
        return {"type": "integer", "value": str(obj)}
    elif isinstance(obj, float):
        return {"type": "float", "value": _normalize_float_str(str(obj))}
    elif isinstance(obj, datetime.datetime):
        val = _normalize_datetime_str(obj.isoformat())
        if obj.tzinfo:
            return {"type": "datetime", "value": val}
        return {"type": "datetime-local", "value": val}
    elif isinstance(obj, datetime.time):
        return {
            "type": "time-local",
            "value": _normalize_localtime_str(str(obj)),
        }
    elif isinstance(obj, datetime.date):
        return {
            "type": "date-local",
            "value": str(obj),
        }
    elif isinstance(obj, list):
        return [convert(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    raise Exception("unsupported type")