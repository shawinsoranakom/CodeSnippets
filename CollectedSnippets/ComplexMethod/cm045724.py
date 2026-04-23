async def __wrapped__(self, input: str, **kwargs) -> np.ndarray:
        """Embed the text using AWS Bedrock.

        Args:
            input: mandatory, the string to embed.
            **kwargs: optional parameters, if unset defaults from the constructor
              will be taken.
        """

        kwargs = {**self.kwargs, **kwargs}
        kwargs = _extract_value_inside_dict(kwargs)

        model_id = kwargs.pop("model_id", None)
        if model_id is None:
            raise ValueError(
                "`model_id` parameter is missing in `BedrockEmbedder`. "
                "Please provide the model ID either in the constructor or in the function call."
            )

        # Build request body based on model type
        request_body: dict[str, Any] = {}
        if "titan" in model_id.lower():
            # Amazon Titan embedding format
            request_body = {"inputText": input}
            if "dimensions" in kwargs:
                request_body["dimensions"] = kwargs.pop("dimensions")
            if "normalize" in kwargs:
                request_body["normalize"] = kwargs.pop("normalize")
        elif "cohere" in model_id.lower():
            # Cohere embedding format
            request_body = {
                "texts": [input],
                "input_type": kwargs.pop("input_type", "search_document"),
            }
            if "truncate" in kwargs:
                request_body["truncate"] = kwargs.pop("truncate")
        else:
            # Generic format - try Titan-style
            request_body = {"inputText": input}

        async with self._session.client("bedrock-runtime") as client:
            response = await client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            # Read and parse response
            response_body = await response["body"].read()
            result = json.loads(response_body)

        # Extract embedding based on model type
        if "titan" in model_id.lower():
            embedding = result.get("embedding", [])
        elif "cohere" in model_id.lower():
            embeddings = result.get("embeddings", [[]])
            embedding = embeddings[0] if embeddings else []
        else:
            # Try common response formats
            embedding = result.get("embedding", result.get("embeddings", [[]])[0])

        return np.array(embedding)