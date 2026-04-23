def extract_bucket_name_and_key_from_headers_and_path(
    headers: dict[str, str], path: str
) -> tuple[str | None, str | None]:
    """
    Extract the bucket name and the object key from a request headers and path. This works with both virtual host
    and path style requests.
    :param headers: the request headers, used to get the Host
    :param path: the request path
    :return: if found, the bucket name and object key
    """
    bucket_name = None
    object_key = None
    host = headers.get("host", "")
    if ".s3" in host:
        vhost_match = _s3_virtual_host_regex.match(host)
        if vhost_match and vhost_match.group("bucket"):
            bucket_name = vhost_match.group("bucket") or None
            split = path.split("/", maxsplit=1)
            if len(split) > 1 and split[1]:
                object_key = split[1]
    else:
        path_without_params = path.partition("?")[0]
        split = path_without_params.split("/", maxsplit=2)
        bucket_name = split[1] or None
        if len(split) > 2:
            object_key = split[2]

    return bucket_name, object_key