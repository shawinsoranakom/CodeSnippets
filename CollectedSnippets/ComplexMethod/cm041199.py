def from_operation(op: OperationModel) -> "_HttpOperation":
        # botocore >= 1.28 might modify the internal model (specifically for S3).
        # It will modify the request URI to strip the bucket name from the path and set the original value at
        # "authPath".
        # Since botocore 1.31.2, botocore will strip the query from the `authPart`
        # We need to add it back from `requestUri` field
        # Use authPath if set, otherwise use the regular requestUri.
        if auth_path := op.http.get("authPath"):
            path, sep, query = op.http.get("requestUri", "").partition("?")
            uri = f"{auth_path.rstrip('/')}{sep}{query}"
        else:
            uri = op.http.get("requestUri")

        method = op.http.get("method")
        deprecated = op.deprecated

        # requestUris can contain mandatory query args (f.e. /apikeys?mode=import)
        path_query = uri.split("?")
        path = path_query[0]
        header_args = []
        query_args: dict[str, list[str]] = {}

        if len(path_query) > 1:
            # parse the query args of the request URI (they are mandatory)
            query_args: dict[str, list[str]] = parse_qs(path_query[1], keep_blank_values=True)
            # for mandatory keys without values, keep an empty list (instead of [''] - the result of parse_qs)
            query_args = {k: filter(None, v) for k, v in query_args.items()}

        # find the required header and query parameters of the input shape
        input_shape = op.input_shape
        if isinstance(input_shape, StructureShape):
            for required_member in input_shape.required_members:
                member_shape = input_shape.members[required_member]
                location = member_shape.serialization.get("location")
                if location is not None:
                    if location == "header":
                        header_name = member_shape.serialization.get("name")
                        header_args.append(header_name)
                    elif location == "querystring":
                        query_name = member_shape.serialization.get("name")
                        # do not overwrite potentially already existing query params with specific values
                        if query_name not in query_args:
                            # an empty list defines a required query param only needs to be present
                            # (no specific value will be enforced when matching)
                            query_args[query_name] = []

        return _HttpOperation(op, path, method, query_args, header_args, deprecated)