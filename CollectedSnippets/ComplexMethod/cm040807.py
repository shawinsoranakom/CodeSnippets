def send_event(self, event, trace_header):
        # Parse the ARN to extract api_id, stage_name, http_method, and resource path
        # Example ARN: arn:{partition}:execute-api:{region}:{account_id}:{api_id}/{stage_name}/{method}/{resource_path}
        arn_parts = parse_arn(self.target["Arn"])
        api_gateway_info = arn_parts["resource"]  # e.g., 'myapi/dev/POST/pets/*/*'
        api_gateway_info_parts = api_gateway_info.split("/")

        api_id = api_gateway_info_parts[0]
        stage_name = api_gateway_info_parts[1]
        http_method = api_gateway_info_parts[2].upper()
        resource_path_parts = api_gateway_info_parts[3:]  # may contain wildcards

        if http_method not in self.ALLOWED_HTTP_METHODS:
            LOG.error("Unsupported HTTP method: %s", http_method)
            return

        # Replace wildcards in resource path with PathParameterValues
        path_params_values = self.target.get("HttpParameters", {}).get("PathParameterValues", [])
        resource_path_segments = []
        path_param_index = 0
        for part in resource_path_parts:
            if part == "*":
                if path_param_index < len(path_params_values):
                    resource_path_segments.append(path_params_values[path_param_index])
                    path_param_index += 1
                else:
                    # Use empty string if no path parameter is provided
                    resource_path_segments.append("")
            else:
                resource_path_segments.append(part)
        resource_path = "/".join(resource_path_segments)

        # Ensure resource path starts and ends with '/'
        resource_path = f"/{resource_path.strip('/')}/"

        # Construct query string parameters
        query_params = self.target.get("HttpParameters", {}).get("QueryStringParameters", {})
        query_string = urlencode(query_params) if query_params else ""

        # Construct headers
        headers = self.target.get("HttpParameters", {}).get("HeaderParameters", {})
        headers = {k: v for k, v in headers.items() if k.lower() not in self.PROHIBITED_HEADERS}
        # Add Host header to ensure proper routing in LocalStack

        host = f"{api_id}.execute-api.localhost.localstack.cloud"
        headers["Host"] = host

        # Ensure Content-Type is set
        headers.setdefault("Content-Type", "application/json")

        # Construct the full URL
        resource_path = f"/{resource_path.strip('/')}/"

        # Construct the full URL using urljoin
        from urllib.parse import urljoin

        base_url = config.internal_service_url()
        base_path = f"/{stage_name}"
        full_path = urljoin(base_path + "/", resource_path.lstrip("/"))
        url = urljoin(base_url + "/", full_path.lstrip("/"))

        if query_string:
            url += f"?{query_string}"

        # Serialize the event, converting datetime objects to strings
        event_json = json.dumps(event, default=str)

        # Add trace header
        headers[TRACE_HEADER_KEY] = trace_header.to_header_str()

        # Send the HTTP request
        response = requests.request(
            method=http_method, url=url, headers=headers, data=event_json, timeout=5
        )
        if not response.ok:
            LOG.warning(
                "API Gateway target invocation failed with status code %s, response: %s",
                response.status_code,
                response.text,
            )