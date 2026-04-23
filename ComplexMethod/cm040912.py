def handle_cors(self, chain: HandlerChain, context: RequestContext, response: Response):
        """
        Handle CORS for S3 requests. S3 CORS rules can be configured.
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/cors.html
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManageCorsUsing.html
        """
        request = context.request
        is_s3, bucket_name = self.pre_parse_s3_request(context.request)

        if not is_s3:
            # continue the chain, let the default CORS handler take care of the request
            return

        # set the service so that the regular CORS enforcer knows it needs to ignore this request
        # we always want to set the service early, because the `ContentDecoder` is very early in the chain and
        # depends on S3
        context.service = self._service

        if config.DISABLE_CUSTOM_CORS_S3:
            # we do not apply S3 specific headers if this config flag is set
            return

        is_options_request = request.method == "OPTIONS"

        def stop_options_chain():
            """
            Stops the chain to avoid the OPTIONS request being parsed. The request is ready to be returned to the
            client. We also need to add specific headers normally added by the serializer for regular requests.
            """
            request_id = context.request_id
            response.headers["x-amz-request-id"] = request_id
            response.headers["x-amz-id-2"] = (
                f"MzRISOwyjmnup{request_id}7/JypPGXLh0OVFGcJaaO3KW/hRAqKOpIEEp"
            )

            response.set_response(b"")
            response.headers.pop("Content-Type", None)
            chain.stop()

        # check the presence of the Origin header. If not there, it means the request is not concerned about CORS
        if not (origin := request.headers.get("Origin")):
            if is_options_request:
                context.operation = self._get_op_from_request(request)
                raise BadRequest(
                    "Insufficient information. Origin request header needed.", HostId=S3_HOST_ID
                )
            else:
                # If the header is missing, Amazon S3 doesn't treat the request as a cross-origin request,
                # and doesn't send CORS response headers in the response.
                return

        is_origin_allowed_by_default = is_origin_allowed_default(request.headers)

        # The bucket does not exist or does have CORS configured
        # might apply default LS CORS or raise AWS specific errors
        if not bucket_name or bucket_name not in self.bucket_cors_index.cors:
            # if the origin is allowed by localstack per default, adds default LS CORS headers
            if is_origin_allowed_by_default:
                add_default_headers(
                    response_headers=response.headers, request_headers=request.headers
                )
                if is_options_request:
                    stop_options_chain()
                return
            # if the origin is not allowed, raise a specific S3 options in case of OPTIONS
            # if it's a regular request, simply return without adding CORS
            else:
                if is_options_request:
                    if not bucket_name:
                        message = "CORSResponse: Bucket not found"
                    else:
                        message = "CORSResponse: CORS is not enabled for this bucket."

                    context.operation = self._get_op_from_request(request)
                    raise AccessForbidden(
                        message,
                        HostId=S3_HOST_ID,
                        Method=request.headers.get("Access-Control-Request-Method", "OPTIONS"),
                        ResourceType="BUCKET",
                    )

                # we return without adding any CORS headers, we could even block the request with 403 here
                return

        rules = self.bucket_cors_index.cors[bucket_name]["CORSRules"]

        if not (rule := self.match_rules(request, rules)):
            if is_options_request:
                context.operation = self._get_op_from_request(request)
                raise AccessForbidden(
                    "CORSResponse: This CORS request is not allowed. This is usually because the evalution of Origin, request method / Access-Control-Request-Method or Access-Control-Request-Headers are not whitelisted by the resource's CORS spec.",
                    HostId=S3_HOST_ID,
                    Method=request.headers.get("Access-Control-Request-Method"),
                    ResourceType="OBJECT",
                )

            if is_options_request:
                stop_options_chain()
            return

        is_wildcard = "*" in rule["AllowedOrigins"]
        # this is contrary to CORS specs. The Access-Control-Allow-Origin should always return the request Origin
        response.headers["Access-Control-Allow-Origin"] = origin if not is_wildcard else "*"
        if not is_wildcard:
            response.headers["Access-Control-Allow-Credentials"] = "true"

        response.headers["Vary"] = (
            "Origin, Access-Control-Request-Headers, Access-Control-Request-Method"
        )

        response.headers["Access-Control-Allow-Methods"] = ", ".join(rule["AllowedMethods"])

        if requested_headers := request.headers.get("Access-Control-Request-Headers"):
            # if the rule matched, it means all Requested Headers are allowed
            requested_headers_formatted = [
                header.strip().lower() for header in requested_headers.split(",")
            ]
            response.headers["Access-Control-Allow-Headers"] = ", ".join(
                requested_headers_formatted
            )

        if expose_headers := rule.get("ExposeHeaders"):
            response.headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)

        if max_age := rule.get("MaxAgeSeconds"):
            response.headers["Access-Control-Max-Age"] = str(max_age)

        if is_options_request:
            stop_options_chain()