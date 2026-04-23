def convert_runnable_to_tool(
    runnable: Runnable,
    args_schema: type[BaseModel] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    arg_types: dict[str, type] | None = None,
) -> BaseTool:
    """Convert a `Runnable` into a `BaseTool`.

    Args:
        runnable: The `Runnable` to convert.
        args_schema: The schema for the tool's input arguments.
        name: The name of the tool.
        description: The description of the tool.
        arg_types: The types of the arguments.

    Returns:
        The tool.
    """
    if args_schema:
        runnable = runnable.with_types(input_type=args_schema)
    description = description or _get_description_from_runnable(runnable)
    name = name or runnable.get_name()

    schema = runnable.input_schema.model_json_schema()
    if schema.get("type") == "string":
        return Tool(
            name=name,
            func=runnable.invoke,
            coroutine=runnable.ainvoke,
            description=description,
        )

    async def ainvoke_wrapper(callbacks: Callbacks | None = None, **kwargs: Any) -> Any:
        return await runnable.ainvoke(kwargs, config={"callbacks": callbacks})

    def invoke_wrapper(callbacks: Callbacks | None = None, **kwargs: Any) -> Any:
        return runnable.invoke(kwargs, config={"callbacks": callbacks})

    if (
        arg_types is None
        and schema.get("type") == "object"
        and schema.get("properties")
    ):
        args_schema = runnable.input_schema
    else:
        args_schema = _get_schema_from_runnable_and_arg_types(
            runnable, name, arg_types=arg_types
        )

    return StructuredTool.from_function(
        name=name,
        func=invoke_wrapper,
        coroutine=ainvoke_wrapper,
        description=description,
        args_schema=args_schema,
    )