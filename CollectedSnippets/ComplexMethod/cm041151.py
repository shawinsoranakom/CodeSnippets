def invoke(self, invocation_context: ApiInvocationContext):
        invocation_path = invocation_context.path_with_query_string
        integration = invocation_context.integration
        path_params = invocation_context.path_params
        relative_path, query_string_params = extract_query_string_params(path=invocation_path)
        uri = integration.get("uri") or integration.get("integrationUri") or ""

        s3 = connect_to().s3
        uri = apply_request_parameters(
            uri,
            integration=integration,
            path_params=path_params,
            query_params=query_string_params,
        )
        uri_match = re.match(self.TARGET_REGEX_PATH_S3_URI, uri) or re.match(
            self.TARGET_REGEX_ACTION_S3_URI, uri
        )
        if not uri_match:
            msg = "Request URI does not match s3 specifications"
            LOG.warning(msg)
            return make_error_response(msg, 400)

        bucket, object_key = uri_match.group("bucket", "object")
        LOG.debug("Getting request for bucket %s object %s", bucket, object_key)

        action = None
        invoke_args = {"Bucket": bucket, "Key": object_key}
        match invocation_context.method:
            case HTTPMethod.GET:
                action = s3.get_object
            case HTTPMethod.PUT:
                invoke_args["Body"] = invocation_context.data
                action = s3.put_object
            case HTTPMethod.DELETE:
                action = s3.delete_object
            case _:
                make_error_response(
                    "The specified method is not allowed against this resource.", 405
                )

        try:
            object = action(**invoke_args)
        except s3.exceptions.NoSuchKey:
            msg = f"Object {object_key} not found"
            LOG.debug(msg)
            return make_error_response(msg, 404)

        headers = mock_aws_request_headers(
            service="s3",
            aws_access_key_id=invocation_context.account_id,
            region_name=invocation_context.region_name,
        )

        if object.get("ContentType"):
            headers["Content-Type"] = object["ContentType"]

        # stream used so large files do not fill memory
        if body := object.get("Body"):
            response = request_response_stream(stream=body, headers=headers)
        else:
            response = requests_response(content="", headers=headers)
        return response