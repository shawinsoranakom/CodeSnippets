def register_tool(
        self,
        tool_name: str,
        tool_path: str,
        schemas: dict = None,
        schema_path: str = "",
        tool_code: str = "",
        tags: list[str] = None,
        tool_source_object=None,  # can be any classes or functions
        include_functions: list[str] = None,
        verbose: bool = False,
    ):
        if self.has_tool(tool_name):
            return

        schema_path = schema_path or TOOL_SCHEMA_PATH / f"{tool_name}.yml"

        if not schemas:
            schemas = make_schema(tool_source_object, include_functions, schema_path)

        if not schemas:
            return

        schemas["tool_path"] = tool_path  # corresponding code file path of the tool
        try:
            ToolSchema(**schemas)  # validation
        except Exception:
            pass
            # logger.warning(
            #     f"{tool_name} schema not conforms to required format, but will be used anyway. Mismatch: {e}"
            # )
        tags = tags or []
        tool = Tool(name=tool_name, path=tool_path, schemas=schemas, code=tool_code, tags=tags)
        self.tools[tool_name] = tool
        for tag in tags:
            self.tools_by_tags[tag].update({tool_name: tool})
        if verbose:
            logger.info(f"{tool_name} registered")
            logger.info(f"schema made at {str(schema_path)}, can be used for checking")