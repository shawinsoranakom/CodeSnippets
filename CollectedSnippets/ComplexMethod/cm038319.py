def _register_module(
        cls,
        module: type[ToolParser],
        module_name: str | list[str] | None = None,
        force: bool = True,
    ) -> None:
        """Register a ToolParser class immediately."""
        if not issubclass(module, ToolParser):
            raise TypeError(
                f"module must be subclass of ToolParser, but got {type(module)}"
            )

        if module_name is None:
            module_name = module.__name__

        if isinstance(module_name, str):
            module_names = [module_name]
        elif is_list_of(module_name, str):
            module_names = module_name
        else:
            raise TypeError("module_name must be str, list[str], or None.")

        for name in module_names:
            if not force and name in cls.tool_parsers:
                existed = cls.tool_parsers[name]
                raise KeyError(f"{name} is already registered at {existed.__module__}")
            cls.tool_parsers[name] = module