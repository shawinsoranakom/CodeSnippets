def map_all_s3_objects(
    s3_client, to_json: bool = True, buckets: str | list[str] = None
) -> dict[str, Any]:
    result = {}
    buckets = ensure_list(buckets)
    if not buckets:
        # get all buckets
        response = s3_client.list_buckets()
        buckets = [b["Name"] for b in response["Buckets"]]

    for bucket in buckets:
        response = s3_client.list_objects_v2(Bucket=bucket)
        objects = [obj["Key"] for obj in response.get("Contents", [])]
        for key in objects:
            value = download_s3_object(s3_client, bucket, key)
            try:
                if to_json:
                    value = json.loads(value)
                separator = "" if key.startswith("/") else "/"
                result[f"{bucket}{separator}{key}"] = value
            except Exception:
                # skip non-JSON or binary objects
                pass
    return result