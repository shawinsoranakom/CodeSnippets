async def make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: dict | None = None,
        body: Any = None,
        timeout: int = 5,
        *,
        follow_redirects: bool = True,
        save_to_file: bool = False,
        include_httpx_metadata: bool = False,
    ) -> Data:
        method = method.upper()
        if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"}:
            msg = f"Unsupported method: {method}"
            raise ValueError(msg)

        processed_body = self._process_body(body)
        redirection_history = []

        try:
            # Prepare request parameters
            request_params = {
                "method": method,
                "url": url,
                "headers": headers,
                "timeout": timeout,
                "follow_redirects": follow_redirects,
            }
            # Only include body for methods that support it (GET must not have a body per HTTP spec)
            if method in {"POST", "PATCH", "PUT", "DELETE"} and processed_body is not None:
                request_params["json"] = processed_body
            response = await client.request(**request_params)

            redirection_history = [
                {
                    "url": redirect.headers.get("Location", str(redirect.url)),
                    "status_code": redirect.status_code,
                }
                for redirect in response.history
            ]

            is_binary, file_path = await self._response_info(response, with_file_path=save_to_file)
            response_headers = self._headers_to_dict(response.headers)

            # Base metadata
            metadata = {
                "source": url,
                "status_code": response.status_code,
                "response_headers": response_headers,
            }

            if redirection_history:
                metadata["redirection_history"] = redirection_history

            if save_to_file:
                mode = "wb" if is_binary else "w"
                encoding = response.encoding if mode == "w" else None
                if file_path:
                    await aiofiles_os.makedirs(file_path.parent, exist_ok=True)
                    if is_binary:
                        async with aiofiles.open(file_path, "wb") as f:
                            await f.write(response.content)
                            await f.flush()
                    else:
                        async with aiofiles.open(file_path, "w", encoding=encoding) as f:
                            await f.write(response.text)
                            await f.flush()
                    metadata["file_path"] = str(file_path)

                if include_httpx_metadata:
                    metadata.update({"headers": headers})
                return Data(data=metadata)

            # Handle response content
            if is_binary:
                result = response.content
            else:
                try:
                    result = response.json()
                except json.JSONDecodeError:
                    self.log("Failed to decode JSON response")
                    result = response.text.encode("utf-8")

            metadata["result"] = result

            if include_httpx_metadata:
                metadata.update({"headers": headers})

            return Data(data=metadata)
        except (httpx.HTTPError, httpx.RequestError, httpx.TimeoutException) as exc:
            self.log(f"Error making request to {url}")
            return Data(
                data={
                    "source": url,
                    "headers": headers,
                    "status_code": 500,
                    "error": str(exc),
                    **({"redirection_history": redirection_history} if redirection_history else {}),
                },
            )