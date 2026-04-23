def _prepare_request_raw(
        self,
        url,
        supplied_headers,
        method,
        params,
        files,
        request_id: Optional[str],
    ) -> Tuple[str, Dict[str, str], Optional[bytes]]:
        abs_url = "%s%s" % (self.base_url, url)
        headers = self._validate_headers(supplied_headers)

        data = None
        if method == "get" or method == "delete":
            if params:
                encoded_params = urlencode([(k, v) for k, v in params.items() if v is not None])
                abs_url = _build_api_url(abs_url, encoded_params)
        elif method in {"post", "put"}:
            if params and files:
                data = params
            if params and not files:
                data = json.dumps(params).encode()
                headers["Content-Type"] = "application/json"
        else:
            raise openai.APIConnectionError(
                message=f"Unrecognized HTTP method {method}. This may indicate a bug in the LLM bindings.",
                request=None,
            )

        headers = self.request_headers(method, headers, request_id)

        # log_debug("Request to LLM API", method=method, path=abs_url)
        # log_debug("Post details", data=data, api_version=self.api_version)

        return abs_url, headers, data