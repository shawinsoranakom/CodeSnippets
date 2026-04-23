def _send_request(self, data: bytes, config: PaddleOCRConfig, callback: Optional[Callable[[float, str], None]]) -> dict[str, Any]:
        """Send request to PaddleOCR API and parse response."""
        # Build payload
        payload = self._build_payload(data, self.file_type, config)

        # Prepare headers
        headers = {"Content-Type": "application/json", "Client-Platform": "ragflow"}
        if config.access_token:
            headers["Authorization"] = f"token {config.access_token}"

        self.logger.info("[PaddleOCR] invoking API")
        if callback:
            callback(0.1, "[PaddleOCR] submitting request")

        # Send request
        try:
            resp = requests.post(config.api_url, json=payload, headers=headers, timeout=self.request_timeout)
            resp.raise_for_status()
        except Exception as exc:
            if callback:
                callback(-1, f"[PaddleOCR] request failed: {exc}")
            raise RuntimeError(f"[PaddleOCR] request failed: {exc}")

        # Parse response
        try:
            response_data = resp.json()
        except Exception as exc:
            raise RuntimeError(f"[PaddleOCR] response is not JSON: {exc}") from exc

        if callback:
            callback(0.8, "[PaddleOCR] response received")

        # Validate response format
        if response_data.get("errorCode") != 0 or not isinstance(response_data.get("result"), dict):
            if callback:
                callback(-1, "[PaddleOCR] invalid response format")
            raise RuntimeError("[PaddleOCR] invalid response format")

        return response_data["result"]