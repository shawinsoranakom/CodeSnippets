def add_cors_headers(request_headers: Headers, response_headers: Headers):
        if ACL_ORIGIN not in response_headers:
            response_headers[ACL_ORIGIN] = (
                request_headers["Origin"]
                if request_headers.get("Origin") and not config.DISABLE_CORS_CHECKS
                else "*"
            )
        if "*" not in response_headers.get(ACL_ORIGIN, ""):
            response_headers[ACL_CREDENTIALS] = "true"
        if ACL_METHODS not in response_headers:
            response_headers[ACL_METHODS] = ",".join(CORS_ALLOWED_METHODS)
        if ACL_ALLOW_HEADERS not in response_headers:
            requested_headers = response_headers.get(ACL_REQUEST_HEADERS, "")
            requested_headers = re.split(r"[,\s]+", requested_headers) + CORS_ALLOWED_HEADERS
            response_headers[ACL_ALLOW_HEADERS] = ",".join([h for h in requested_headers if h])
        if ACL_EXPOSE_HEADERS not in response_headers:
            response_headers[ACL_EXPOSE_HEADERS] = ",".join(CORS_EXPOSE_HEADERS)
        if (
            request_headers.get(ACL_REQUEST_PRIVATE_NETWORK) == "true"
            and ACL_ALLOW_PRIVATE_NETWORK not in response_headers
        ):
            response_headers[ACL_ALLOW_PRIVATE_NETWORK] = "true"

        # we conditionally apply CORS headers depending on the Origin, so add it to `Vary`
        response_headers["Vary"] = "Origin"