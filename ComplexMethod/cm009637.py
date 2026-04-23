def convert_to_openai_function(
    function: Mapping[str, Any] | type | Callable | BaseTool,
    *,
    strict: bool | None = None,
) -> dict[str, Any]:
    """Convert a raw function/class to an OpenAI function.

    Args:
        function: A dictionary, Pydantic `BaseModel` class, `TypedDict` class, a
            LangChain `Tool` object, or a Python function.

            If a dictionary is passed in, it is assumed to already be a valid OpenAI
            function, a JSON schema with top-level `title` key specified, an Anthropic
            format tool, or an Amazon Bedrock Converse format tool.
        strict: If `True`, model output is guaranteed to exactly match the JSON Schema
            provided in the function definition.

            If `None`, `strict` argument will not be included in function definition.

    Returns:
        A dict version of the passed in function which is compatible with the OpenAI
            function-calling API.

    Raises:
        ValueError: If function is not in a supported format.

    !!! warning "Behavior changed in `langchain-core` 0.3.16"

        `description` and `parameters` keys are now optional. Only `name` is
        required and guaranteed to be part of the output.
    """
    # an Anthropic format tool
    if isinstance(function, dict) and all(
        k in function for k in ("name", "input_schema")
    ):
        oai_function = {
            "name": function["name"],
            "parameters": function["input_schema"],
        }
        if "description" in function:
            oai_function["description"] = function["description"]
    # an Amazon Bedrock Converse format tool
    elif isinstance(function, dict) and "toolSpec" in function:
        oai_function = {
            "name": function["toolSpec"]["name"],
            "parameters": function["toolSpec"]["inputSchema"]["json"],
        }
        if "description" in function["toolSpec"]:
            oai_function["description"] = function["toolSpec"]["description"]
    # already in OpenAI function format
    elif isinstance(function, dict) and "name" in function:
        oai_function = {
            k: v
            for k, v in function.items()
            if k in {"name", "description", "parameters", "strict"}
        }
    # a JSON schema with title and description
    elif isinstance(function, dict) and "title" in function:
        function_copy = function.copy()
        oai_function = {"name": function_copy.pop("title")}
        if "description" in function_copy:
            oai_function["description"] = function_copy.pop("description")
        if function_copy and "properties" in function_copy:
            oai_function["parameters"] = function_copy
    elif isinstance(function, type) and is_basemodel_subclass(function):
        oai_function = cast("dict", _convert_pydantic_to_openai_function(function))
    elif is_typeddict(function):
        oai_function = cast(
            "dict", _convert_typed_dict_to_openai_function(cast("type", function))
        )
    elif isinstance(function, langchain_core.tools.base.BaseTool):
        oai_function = cast("dict", _format_tool_to_openai_function(function))
    elif callable(function):
        oai_function = cast(
            "dict", _convert_python_function_to_openai_function(function)
        )
    else:
        if isinstance(function, dict) and (
            "type" in function or "properties" in function
        ):
            msg = (
                f"Unsupported function\n\n{function}\n\nTo use a JSON schema as a "
                "function, it must have a top-level 'title' key to be used as the "
                "function name."
            )
            raise ValueError(msg)
        msg = (
            f"Unsupported function\n\n{function}\n\nFunctions must be passed in"
            " as Dict, pydantic.BaseModel, or Callable. If they're a dict they must"
            " either be in OpenAI function format or valid JSON schema with top-level"
            " 'title' key."
        )
        raise ValueError(msg)

    if strict is not None:
        if "strict" in oai_function and oai_function["strict"] != strict:
            msg = (
                f"Tool/function already has a 'strict' key with value "
                f"{oai_function['strict']} which is different from the explicit "
                f"`strict` arg received {strict=}."
            )
            raise ValueError(msg)
        oai_function["strict"] = strict
        if strict:
            # All fields must be `required`
            parameters = oai_function.get("parameters")
            if isinstance(parameters, dict):
                fields = parameters.get("properties")
                if isinstance(fields, dict) and fields:
                    parameters = dict(parameters)
                    parameters["required"] = list(fields.keys())
                    oai_function["parameters"] = parameters

            # As of 08/06/24, OpenAI requires that additionalProperties be supplied and
            # set to False if strict is True.
            # All properties layer needs 'additionalProperties=False'
            oai_function["parameters"] = _recursive_set_additional_properties_false(
                oai_function["parameters"]
            )
    return oai_function