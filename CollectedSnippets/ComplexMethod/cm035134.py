def _call_api(self, data: str, file_type: FileType) -> tuple[str, dict[str, Any]]:
        """Call the PaddleOCR-VL API and return extracted text and raw response."""

        request_data: dict[str, Any] = {
            "file": data,
            "fileType": file_type,
        }
        request_data.update(self._service_params)

        try:
            request_model = PaddleOCRVLInferRequest(**request_data)
            request_payload = request_model.model_dump(exclude_none=True)
        except Exception as exc:  # pragma: no cover - defensive
            msg = f"Invalid request parameters for PaddleOCR-VL: {exc}"
            raise ValueError(msg) from exc

        headers = {
            "Content-Type": "application/json",
            "Client-Platform": "langchain",
        }
        if self.access_token is not None:
            headers["Authorization"] = f"token {self.access_token.get_secret_value()}"

        try:
            response = requests.post(
                self.api_url,
                json=request_payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f"Failed to call PaddleOCR-VL API: {exc}"
            raise ValueError(msg) from exc

        try:
            response_data: dict[str, Any] = response.json()
        except ValueError as exc:  # pragma: no cover - defensive
            msg = f"Invalid JSON response from PaddleOCR-VL API: {exc}"
            raise ValueError(msg) from exc

        if "result" not in response_data:
            msg = "Response from PaddleOCR-VL API is missing the 'result' field."
            raise ValueError(msg)

        try:
            result = PaddleOCRVLInferResult(**response_data["result"])
        except Exception as exc:  # pragma: no cover - defensive
            msg = f"Invalid response format from PaddleOCR-VL API: {exc}"
            raise ValueError(msg) from exc

        text_parts = [
            layout_result.markdown.text
            for layout_result in result.layoutParsingResults
            if layout_result.markdown and layout_result.markdown.text
        ]
        text = _PAGES_DELIMITER.join(text_parts)

        return text, response_data