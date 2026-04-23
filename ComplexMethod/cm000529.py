async def run(
        self, input_data: Input, *, execution_context: ExecutionContext, **kwargs
    ) -> BlockOutput:
        # ─── Parse/normalise body ────────────────────────────────────
        body = input_data.body
        if isinstance(body, str):
            try:
                # Validate JSON string length to prevent DoS attacks
                if len(body) > 10_000_000:  # 10MB limit
                    raise ValueError("JSON body too large")

                parsed_body = json.loads(body)

                # Validate that parsed JSON is safe (basic object/array/primitive types)
                if (
                    isinstance(parsed_body, (dict, list, str, int, float, bool))
                    or parsed_body is None
                ):
                    body = parsed_body
                else:
                    # Unexpected type, treat as plain text
                    input_data.json_format = False

            except (json.JSONDecodeError, ValueError):
                # Invalid JSON or too large – treat as form‑field value instead
                input_data.json_format = False

        # ─── Prepare files (if any) ──────────────────────────────────
        use_files = bool(input_data.files)
        files_payload: list[tuple[str, tuple[str, BytesIO, str]]] = []
        if use_files:
            files_payload = await self._prepare_files(
                execution_context, input_data.files_name, input_data.files
            )

        # Enforce body format rules
        if use_files and input_data.json_format:
            raise ValueError(
                "json_format=True cannot be combined with file uploads; set json_format=False and put form fields in `body`."
            )

        # ─── Execute request ─────────────────────────────────────────
        # Use raise_for_status=False so HTTP errors (4xx, 5xx) are returned
        # as response objects instead of raising exceptions, allowing proper
        # handling via client_error and server_error outputs
        response = await Requests(
            raise_for_status=False,
            retry_max_attempts=1,  # allow callers to handle HTTP errors immediately
        ).request(
            input_data.method.value,
            input_data.url,
            headers=input_data.headers,
            files=files_payload if use_files else None,
            # * If files → multipart ⇒ pass form‑fields via data=
            data=body if not input_data.json_format else None,
            # * Else, choose JSON vs url‑encoded based on flag
            json=body if (input_data.json_format and not use_files) else None,
        )

        # Decide how to parse the response
        if response.headers.get("content-type", "").startswith("application/json"):
            result = None if response.status == 204 else response.json()
        else:
            result = response.text()

        # Yield according to status code bucket
        if 200 <= response.status < 300:
            yield "response", result
        elif 400 <= response.status < 500:
            yield "client_error", result
        else:
            yield "server_error", result