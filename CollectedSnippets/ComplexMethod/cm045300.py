async def run(self, args: BaseModel, cancellation_token: CancellationToken) -> Any:
        """Execute the HTTP tool with the given arguments.

        Args:
            args: The validated input arguments
            cancellation_token: Token for cancelling the operation

        Returns:
            The response body from the HTTP call in JSON format

        Raises:
            Exception: If tool execution fails
        """

        model_dump = args.model_dump()
        path_params = {k: v for k, v in model_dump.items() if k in self._path_params}
        # Remove path params from the model dump
        for k in self._path_params:
            model_dump.pop(k)

        path = self.server_params.path.format(**path_params)

        url = httpx.URL(
            scheme=self.server_params.scheme,
            host=self.server_params.host,
            port=self.server_params.port,
            path=path,
        )
        timeout_config = httpx.Timeout(timeout=self.server_params.timeout)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            match self.server_params.method:
                case "GET":
                    response = await client.get(url, headers=self.server_params.headers, params=model_dump)
                case "PUT":
                    response = await client.put(url, headers=self.server_params.headers, json=model_dump)
                case "DELETE":
                    response = await client.delete(url, headers=self.server_params.headers, params=model_dump)
                case "PATCH":
                    response = await client.patch(url, headers=self.server_params.headers, json=model_dump)
                case _:  # Default case POST
                    response = await client.post(url, headers=self.server_params.headers, json=model_dump)

        match self.server_params.return_type:
            case "text":
                return response.text
            case "json":
                return response.json()
            case _:
                raise ValueError(f"Invalid return type: {self.server_params.return_type}")