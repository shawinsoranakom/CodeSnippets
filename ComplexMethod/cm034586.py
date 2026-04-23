def to_string(value) -> str:
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        if "text" in value:
            return value["text"]
        elif "name" in value:
            return ""
        elif "bucket_id" in value:
            bucket_dir = Path(get_bucket_dir(value.get("bucket_id")))
            return "".join(read_bucket(bucket_dir))
        return ""
    elif isinstance(value, list):
        return "".join([to_string(v) for v in value if v.get("type", "text") == "text"])
    elif value is None:
        return ""
    return str(value)