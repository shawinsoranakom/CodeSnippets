def _reverse_inject_signature_hmac_v1_query(
    request: Request,
) -> tuple[urlparse.SplitResult, HTTPHeaders]:
    """
    Reverses what does HmacV1QueryAuth._inject_signature while injecting the signature in the request.
    Transforms the query string parameters in headers to recalculate the signature
    see botocore.auth.HmacV1QueryAuth._inject_signature
    :param request: the original request
    :return: tuple of a split result from the reversed request, and the reversed headers
    """
    new_headers = {}
    new_query_string_dict = {}

    for header, value in request.args.items():
        header_low = header.lower()
        if header_low not in HmacV1QueryAuthValidation.post_signature_headers:
            new_headers[header] = value
        elif header_low in HmacV1QueryAuthValidation.QSAOfInterest_low:
            new_query_string_dict[header] = value

    # there should not be any headers here. If there are, it means they have been added by the client
    # We should verify them, they will fail the signature except if they were part of the original request
    for header, value in request.headers.items():
        header_low = header.lower()
        if header_low.startswith("x-amz-") or header_low in ["content-type", "date", "content-md5"]:
            new_headers[header_low] = value

    # rebuild the query string
    new_query_string = percent_encode_sequence(new_query_string_dict)

    if bucket_name := uses_host_addressing(request.headers):
        # if the request is host addressed, we need to remove the bucket from the host and set it in the path
        path = f"/{bucket_name}{request.path}"
        host = request.host.removeprefix(f"{bucket_name}.")
    else:
        path = request.path
        host = request.host

    # we need to URL encode the path, as the key needs to be urlencoded for the signature to match
    encoded_path = urlparse.quote(path)

    reversed_url = f"{request.scheme}://{host}{encoded_path}?{new_query_string}"

    reversed_headers = HTTPHeaders()
    for key, value in new_headers.items():
        reversed_headers[key] = value

    return urlsplit(reversed_url), reversed_headers