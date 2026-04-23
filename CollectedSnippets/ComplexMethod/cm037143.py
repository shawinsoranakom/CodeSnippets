def get_parser(
        cls,
        tool_parser_name: str | None = None,
        reasoning_parser_name: str | None = None,
        enable_auto_tools: bool = False,
        model_name: str | None = None,
    ) -> type[Parser] | None:
        """
        Get a unified Parser that handles both reasoning and tool parsing.

        This method checks if a unified Parser exists that can handle both
        reasoning extraction and tool call parsing. If no unified parser
        exists, it creates a DelegatingParser that wraps the individual
        reasoning and tool parsers.

        Args:
            tool_parser_name: The name of the tool parser.
            reasoning_parser_name: The name of the reasoning parser.
            enable_auto_tools: Whether auto tool choice is enabled.
            model_name: The model name for parser-specific warnings.

        Returns:
            A Parser class, or None if neither parser is specified.
        """
        from vllm.parser.abstract_parser import _WrappedParser

        if not tool_parser_name and not reasoning_parser_name:
            return None

        # Strategy 1: If both names match, check for a unified parser with that name
        if tool_parser_name and tool_parser_name == reasoning_parser_name:
            try:
                parser = cls.get_parser_internal(tool_parser_name)
                logger.info(
                    "Using unified parser '%s' for both reasoning and tool parsing.",
                    tool_parser_name,
                )
                return parser
            except KeyError:
                pass  # No unified parser with this name

        # Strategy 2: Check for parser with either name
        for name in [tool_parser_name, reasoning_parser_name]:
            if name:
                try:
                    parser = cls.get_parser_internal(name)
                    logger.info(
                        "Using unified parser '%s' for reasoning and tool parsing.",
                        name,
                    )
                    return parser
                except KeyError:
                    pass

        # Strategy 3: Create a DelegatingParser with the individual parser classes
        reasoning_parser_cls = cls.get_reasoning_parser(reasoning_parser_name)
        tool_parser_cls = cls.get_tool_parser(
            tool_parser_name, enable_auto_tools, model_name
        )

        if reasoning_parser_cls is None and tool_parser_cls is None:
            return None

        # Set the class-level attributes on the imported _WrappedParser
        _WrappedParser.reasoning_parser_cls = reasoning_parser_cls
        _WrappedParser.tool_parser_cls = tool_parser_cls

        return _WrappedParser