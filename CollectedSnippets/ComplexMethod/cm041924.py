async def acall(
        cls,
        model: str,
        prompt: Any = None,
        history: list = None,
        api_key: str = None,
        messages: List[Message] = None,
        plugins: Union[str, Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[GenerationResponse, AsyncGenerator[GenerationResponse, None]]:
        if (prompt is None or not prompt) and (messages is None or not messages):
            raise InputRequired("prompt or messages is required!")
        if model is None or not model:
            raise ModelRequired("Model is required!")
        task_group, function = "aigc", "generation"  # fixed value
        if plugins is not None:
            headers = kwargs.pop("headers", {})
            if isinstance(plugins, str):
                headers["X-DashScope-Plugin"] = plugins
            else:
                headers["X-DashScope-Plugin"] = json.dumps(plugins)
            kwargs["headers"] = headers
        input, parameters = cls._build_input_parameters(model, prompt, history, messages, **kwargs)

        api_key, model = BaseAioApi._validate_params(api_key, model)
        request = build_api_arequest(
            model=model,
            input=input,
            task_group=task_group,
            task=Generation.task,
            function=function,
            api_key=api_key,
            **kwargs,
        )
        response = await request.aio_call()
        is_stream = kwargs.get("stream", False)
        if is_stream:

            async def aresp_iterator(response):
                async for resp in response:
                    yield GenerationResponse.from_api_response(resp)

            return aresp_iterator(response)
        else:
            return GenerationResponse.from_api_response(response)