def _headers_of(parameters: TaskParameters) -> dict | None:
        headers = parameters.get("Headers", {})
        if headers:
            for key in headers.keys():
                # TODO: the following check takes place at parse time.
                if key in StateTaskServiceApiGateway._FORBIDDEN_HTTP_HEADERS:
                    raise ValueError(f"The 'Headers' field contains unsupported values: {key}")
                for forbidden_prefix in StateTaskServiceApiGateway._FORBIDDEN_HTTP_HEADERS_PREFIX:
                    if key.startswith(forbidden_prefix):
                        raise ValueError(f"The 'Headers' field contains unsupported values: {key}")

                value = headers.get(key)
                if isinstance(value, list):
                    headers[key] = f"[{','.join(value)}]"

            if "RequestBody" in parameters:
                headers[HEADER_CONTENT_TYPE] = APPLICATION_JSON
        headers["Accept"] = APPLICATION_JSON
        return headers