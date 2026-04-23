async def _call_service(
        self,
        processed_input: str,
        file_type: Optional[str],
        ctx: Context,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not self._server_url:
            raise RuntimeError("Server URL not configured")

        endpoint = self._get_service_endpoint()
        if endpoint:
            endpoint = "/" + endpoint
        url = f"{self._server_url.rstrip('/')}{endpoint}"

        payload = self._prepare_service_payload(processed_input, file_type, **kwargs)
        headers = {"Content-Type": "application/json"}

        if self._ppocr_source == "aistudio":
            if not self._aistudio_access_token:
                raise RuntimeError("Missing AI Studio access token")
            headers["Authorization"] = f"token {self._aistudio_access_token}"
        elif self._ppocr_source == "qianfan":
            if not self._qianfan_api_key:
                raise RuntimeError("Missing Qianfan API key")
            headers["Authorization"] = f"Bearer {self._qianfan_api_key}"

        try:
            timeout = httpx.Timeout(
                connect=30.0, read=self._timeout, write=30.0, pool=30.0
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"HTTP request failed: {type(e).__name__}: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid service response: {str(e)}")