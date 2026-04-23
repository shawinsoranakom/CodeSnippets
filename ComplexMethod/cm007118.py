async def get_models(self, base_url_value: str, *, tool_model_enabled: bool | None = None) -> list[str]:
        """Fetches a list of models from the Ollama API suitable for text generation.

        Args:
            base_url_value (str): The base URL of the Ollama API.
            tool_model_enabled (bool | None, optional): If True, filters the models further to include
                only those that support tool calling. Defaults to None.

        Returns:
            list[str]: A list of model names suitable for text generation. Models are included if:
                - They have the "completion" capability, OR
                - The capabilities field is not returned (backwards compatibility with older Ollama versions)
                If `tool_model_enabled` is True, only models with verified "tools" capability are included
                (models without capabilities info are excluded in this case).

        Raises:
            ValueError: If there is an issue with the API request or response, or if the model
                names cannot be retrieved.
        """
        try:
            # Strip /v1 suffix if present, as Ollama API endpoints are at root level
            base_url = base_url_value.rstrip("/").removesuffix("/v1")
            if not base_url.endswith("/"):
                base_url = base_url + "/"
            base_url = transform_localhost_url(base_url)

            # Ollama REST API to return models
            tags_url = urljoin(base_url, "api/tags")

            # Ollama REST API to return model capabilities
            show_url = urljoin(base_url, "api/show")

            async with httpx.AsyncClient() as client:
                headers = self.headers
                # Fetch available models
                tags_response = await client.get(url=tags_url, headers=headers)
                tags_response.raise_for_status()
                models = tags_response.json()
                if asyncio.iscoroutine(models):
                    models = await models
                await logger.adebug(f"Available models: {models}")

                # Filter models that are NOT embedding models
                model_ids = []
                for model in models[self.JSON_MODELS_KEY]:
                    model_name = model[self.JSON_NAME_KEY]
                    await logger.adebug(f"Checking model: {model_name}")

                    payload = {"model": model_name}
                    show_response = await client.post(url=show_url, json=payload, headers=headers)
                    show_response.raise_for_status()
                    json_data = show_response.json()
                    if asyncio.iscoroutine(json_data):
                        json_data = await json_data

                    capabilities = json_data.get(self.JSON_CAPABILITIES_KEY)
                    await logger.adebug(f"Model: {model_name}, Capabilities: {capabilities}")

                    # If capabilities not provided, assume it's a completion model (backwards compatibility
                    # with older Ollama versions that don't return capabilities from /api/show)
                    if capabilities is None:
                        if not tool_model_enabled:
                            model_ids.append(model_name)
                        # If tool_model_enabled is True but no capabilities info, skip the model
                        # since we can't verify tool support
                    elif self.DESIRED_CAPABILITY in capabilities and (
                        not tool_model_enabled or self.TOOL_CALLING_CAPABILITY in capabilities
                    ):
                        model_ids.append(model_name)

        except (httpx.RequestError, ValueError) as e:
            msg = "Could not get model names from Ollama."
            raise ValueError(msg) from e

        return model_ids