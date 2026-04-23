def _extract_service_indicators(request: Request) -> _ServiceIndicators:
    """Extracts all different fields that might indicate which service a request is targeting."""
    x_amz_target = request.headers.get("x-amz-target")
    authorization = request.headers.get("authorization")
    is_rpc_v2 = "rpc-v2-cbor" in request.headers.get("Smithy-Protocol", "")

    signing_name = None
    if authorization:
        try:
            auth_type, auth_info = authorization.split(None, 1)
            auth_type = auth_type.lower().strip()
            if auth_type == "aws4-hmac-sha256":
                values = parse_dict_header(auth_info)
                _, _, _, signing_name, _ = values["Credential"].split("/")
        except (ValueError, KeyError):
            LOG.debug("auth header could not be parsed for service routing: %s", authorization)
            pass
    if is_rpc_v2:
        # https://smithy.io/2.0/additional-specs/protocols/smithy-rpc-v2.html#requests
        rpc_v2_params = request.path.lstrip("/").split("/")
        if len(rpc_v2_params) >= 4:
            *_, service_shape_name, __, operation = rpc_v2_params
            target_prefix = service_shape_name.split("#")[-1]
        else:
            target_prefix, operation = None, None
    elif x_amz_target:
        if "." in x_amz_target:
            target_prefix, operation = x_amz_target.split(".", 1)
        else:
            target_prefix = None
            operation = x_amz_target
    else:
        target_prefix, operation = None, None

    return _ServiceIndicators(signing_name, target_prefix, operation, request.host, request.path)