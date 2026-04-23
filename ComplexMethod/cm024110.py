async def _param_cgi_response(
            _method: str, url: URL, data: dict[str, Any] | None
        ) -> AiohttpClientMockResponse:
            group = (data or {}).get("group")
            if group == "root.Brand":
                return _text_response(url, BRAND_RESPONSE)
            if group == "root.Image":
                return _text_response(url, IMAGE_RESPONSE)
            if group == "root.Input":
                return _text_response(url, PORTS_RESPONSE)
            if group == "root.IOPort":
                return _text_response(url, param_ports_payload)
            if group == "root.Output":
                return _text_response(url, PORTS_RESPONSE)
            if group == "root.Properties":
                return _text_response(url, param_properties_payload)
            if group == "root.PTZ":
                return _text_response(url, PTZ_RESPONSE)
            if group == "root.StreamProfile":
                return _text_response(url, STREAM_PROFILES_RESPONSE)
            return _text_response(url, "")