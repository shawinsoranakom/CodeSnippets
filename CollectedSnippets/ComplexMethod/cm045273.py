def _check_cache(
        self,
        messages: Sequence[LLMMessage],
        tools: Sequence[Tool | ToolSchema],
        json_output: Optional[bool | type[BaseModel]],
        extra_create_args: Mapping[str, Any],
    ) -> tuple[Optional[Union[CreateResult, List[Union[str, CreateResult]]]], str]:
        """
        Helper function to check the cache for a result.
        Returns a tuple of (cached_result, cache_key).
        """

        json_output_data: str | bool | None = None

        if isinstance(json_output, type) and issubclass(json_output, BaseModel):
            json_output_data = json.dumps(json_output.model_json_schema())
        elif isinstance(json_output, bool):
            json_output_data = json_output

        data = {
            "messages": [message.model_dump() for message in messages],
            "tools": [(tool.schema if isinstance(tool, Tool) else tool) for tool in tools],
            "json_output": json_output_data,
            "extra_create_args": extra_create_args,
        }
        serialized_data = json.dumps(data, sort_keys=True)
        cache_key = hashlib.sha256(serialized_data.encode()).hexdigest()

        cached_result = self.store.get(cache_key)
        if cached_result is not None:
            # Handle case where cache store returns dict instead of CreateResult (e.g., Redis)
            if isinstance(cached_result, dict):
                try:
                    cached_result = CreateResult.model_validate(cached_result)
                except ValidationError:
                    # If reconstruction fails, treat as cache miss
                    return None, cache_key
            elif isinstance(cached_result, list):
                # Handle streaming results - reconstruct CreateResult instances from dicts
                try:
                    reconstructed_list: List[Union[str, CreateResult]] = []
                    for item in cached_result:
                        if isinstance(item, dict):
                            reconstructed_list.append(CreateResult.model_validate(item))
                        else:
                            reconstructed_list.append(item)
                    cached_result = reconstructed_list
                except ValidationError:
                    # If reconstruction fails, treat as cache miss
                    return None, cache_key
            elif isinstance(cached_result, str):
                # Handle case where cache store returns a string (e.g., Redis with decode errors)
                try:
                    # Try to parse the string as JSON and reconstruct CreateResult
                    parsed_data = json.loads(cached_result)
                    if isinstance(parsed_data, dict):
                        cached_result = CreateResult.model_validate(parsed_data)
                    elif isinstance(parsed_data, list):
                        # Handle streaming results stored as JSON string
                        reconstructed_list_2: list[CreateResult | str] = []
                        for item in parsed_data:  # type: ignore[reportUnknownVariableType]
                            if isinstance(item, dict):
                                reconstructed_list_2.append(CreateResult.model_validate(item))
                            elif isinstance(item, str):
                                reconstructed_list_2.append(item)
                            else:
                                # If item is neither dict nor str, treat as cache miss
                                return None, cache_key
                        cached_result = reconstructed_list_2
                    else:
                        # If parsed data is not dict or list, treat as cache miss
                        return None, cache_key
                except (json.JSONDecodeError, ValidationError):
                    # If JSON parsing or validation fails, treat as cache miss
                    return None, cache_key
            # If it's already the right type (CreateResult or list), return as-is
            return cached_result, cache_key

        return None, cache_key