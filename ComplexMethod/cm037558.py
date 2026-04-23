def _register_module(
        cls,
        module: type[ReasoningParser],
        module_name: str | list[str] | None = None,
        force: bool = True,
    ) -> None:
        """Register a ReasoningParser class immediately."""
        if not issubclass(module, ReasoningParser):
            raise TypeError(
                f"module must be subclass of ReasoningParser, but got {type(module)}"
            )

        if module_name is None:
            module_names = [module.__name__]
        elif isinstance(module_name, str):
            module_names = [module_name]
        elif is_list_of(module_name, str):
            module_names = module_name
        else:
            raise TypeError("module_name must be str, list[str], or None.")

        for name in module_names:
            if not force and name in cls.reasoning_parsers:
                existed = cls.reasoning_parsers[name]
                raise KeyError(f"{name} is already registered at {existed.__module__}")
            cls.reasoning_parsers[name] = module