async def handle(self, request: web.Request):
        if self._format == "raw":
            payload = {QUERY_SCHEMA_COLUMN: await request.text()}
        elif self._format == "custom":
            try:
                payload = await request.json()
            except json.decoder.JSONDecodeError:
                payload = {}
            query_params = request.query
            for param, value in query_params.items():
                if param not in payload:
                    payload[param] = value
        logging.info(
            json.dumps(
                {
                    "_type": "request_payload",
                    "session_id": request.headers.get("X-Pathway-Session"),
                    "payload": payload,
                }
            )
        )
        self._verify_payload(payload)
        if self._request_validator:
            try:
                validator_ret = self._request_validator(payload, request.headers)
                if validator_ret is not None:
                    raise Exception(validator_ret)
            except Exception as e:
                record = {
                    "_type": "validator_rejected_http_request",
                    "error": str(e),
                    "payload": payload,
                }
                logging.error(json.dumps(record))
                raise web.HTTPBadRequest(reason=str(e))

        result = await self._request_processor(
            json.dumps(payload, sort_keys=True, ensure_ascii=False)
        )
        return copy.deepcopy(result)