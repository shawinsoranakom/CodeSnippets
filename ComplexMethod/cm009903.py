def openapi_spec_to_openai_fn(
    spec: OpenAPISpec,
) -> tuple[list[dict[str, Any]], Callable]:
    """OpenAPI spec to OpenAI function JSON Schema.

    Convert a valid OpenAPI spec to the JSON Schema format expected for OpenAI
    functions.

    Args:
        spec: OpenAPI spec to convert.

    Returns:
        Tuple of the OpenAI functions JSON schema and a default function for executing
            a request based on the OpenAI function schema.
    """
    try:
        from langchain_community.tools import APIOperation
    except ImportError as e:
        msg = (
            "Could not import langchain_community.tools. "
            "Please install it with `pip install langchain-community`."
        )
        raise ImportError(msg) from e

    if not spec.paths:
        return [], lambda: None
    functions = []
    _name_to_call_map = {}
    for path in spec.paths:
        path_params = {
            (p.name, p.param_in): p for p in spec.get_parameters_for_path(path)
        }
        for method in spec.get_methods_for_path(path):
            request_args = {}
            op = spec.get_operation(path, method)
            op_params = path_params.copy()
            for param in spec.get_parameters_for_operation(op):
                op_params[(param.name, param.param_in)] = param
            params_by_type = defaultdict(list)
            for name_loc, p in op_params.items():
                params_by_type[name_loc[1]].append(p)
            param_loc_to_arg_name = {
                "query": "params",
                "header": "headers",
                "cookie": "cookies",
                "path": "path_params",
            }
            for param_loc, arg_name in param_loc_to_arg_name.items():
                if params_by_type[param_loc]:
                    request_args[arg_name] = _openapi_params_to_json_schema(
                        params_by_type[param_loc],
                        spec,
                    )
            request_body = spec.get_request_body_for_operation(op)
            # TODO: Support more MIME types.
            if request_body and request_body.content:
                media_types = {}
                for media_type, media_type_object in request_body.content.items():
                    if media_type_object.media_type_schema:
                        schema = spec.get_schema(media_type_object.media_type_schema)
                        media_types[media_type] = json.loads(
                            schema.json(exclude_none=True),
                        )
                if len(media_types) == 1:
                    media_type, schema_dict = next(iter(media_types.items()))
                    key = "json" if media_type == "application/json" else "data"
                    request_args[key] = schema_dict
                elif len(media_types) > 1:
                    request_args["data"] = {"anyOf": list(media_types.values())}

            api_op = APIOperation.from_openapi_spec(spec, path, method)
            fn = {
                "name": api_op.operation_id,
                "description": api_op.description,
                "parameters": {
                    "type": "object",
                    "properties": request_args,
                },
            }
            functions.append(fn)
            _name_to_call_map[fn["name"]] = {
                "method": method,
                "url": api_op.base_url + api_op.path,
            }

    def default_call_api(
        name: str,
        fn_args: dict,
        headers: dict | None = None,
        params: dict | None = None,
        timeout: int | None = 30,
        **kwargs: Any,
    ) -> Any:
        method = _name_to_call_map[name]["method"]
        url = _name_to_call_map[name]["url"]
        path_params = fn_args.pop("path_params", {})
        url = _format_url(url, path_params)
        if "data" in fn_args and isinstance(fn_args["data"], dict):
            fn_args["data"] = json.dumps(fn_args["data"])
        _kwargs = {**fn_args, **kwargs}
        if headers is not None:
            if "headers" in _kwargs:
                _kwargs["headers"].update(headers)
            else:
                _kwargs["headers"] = headers
        if params is not None:
            if "params" in _kwargs:
                _kwargs["params"].update(params)
            else:
                _kwargs["params"] = params
        return requests.request(method, url, **_kwargs, timeout=timeout)

    return functions, default_call_api