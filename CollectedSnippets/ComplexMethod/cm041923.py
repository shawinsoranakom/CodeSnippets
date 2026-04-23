def build_api_arequest(
    model: str, input: object, task_group: str, task: str, function: str, api_key: str, is_service=True, **kwargs
):
    (
        api_protocol,
        ws_stream_mode,
        is_binary_input,
        http_method,
        stream,
        async_request,
        query,
        headers,
        request_timeout,
        form,
        resources,
        base_address,
        _,
    ) = _get_protocol_params(kwargs)
    task_id = kwargs.pop("task_id", None)
    if api_protocol in [ApiProtocol.HTTP, ApiProtocol.HTTPS]:
        if base_address is None:
            base_address = dashscope.base_http_api_url
        if not base_address.endswith("/"):
            http_url = base_address + "/"
        else:
            http_url = base_address

        if is_service:
            http_url = http_url + SERVICE_API_PATH + "/"

        if task_group:
            http_url += "%s/" % task_group
        if task:
            http_url += "%s/" % task
        if function:
            http_url += function
        request = AioHttpRequest(
            url=http_url,
            api_key=api_key,
            http_method=http_method,
            stream=stream,
            async_request=async_request,
            query=query,
            timeout=request_timeout,
            task_id=task_id,
        )
    else:
        raise UnsupportedApiProtocol("Unsupported protocol: %s, support [http, https, websocket]" % api_protocol)

    if headers is not None:
        request.add_headers(headers=headers)

    if input is None and form is None:
        raise InputDataRequired("There is no input data and form data")

    request_data = ApiRequestData(
        model,
        task_group=task_group,
        task=task,
        function=function,
        input=input,
        form=form,
        is_binary_input=is_binary_input,
        api_protocol=api_protocol,
    )
    request_data.add_resources(resources)
    request_data.add_parameters(**kwargs)
    request.data = request_data
    return request