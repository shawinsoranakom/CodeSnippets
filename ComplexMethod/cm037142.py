def _register_module(
        cls,
        module: type[Parser],
        module_name: str | list[str] | None = None,
        force: bool = True,
    ) -> None:
        """Register a Parser class immediately."""
        from vllm.parser.abstract_parser import Parser

        if not issubclass(module, Parser):
            raise TypeError(
                f"module must be subclass of Parser, but got {type(module)}"
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
            if not force and name in cls.parsers:
                existed = cls.parsers[name]
                raise KeyError(f"{name} is already registered at {existed.__module__}")
            cls.parsers[name] = module