def visit(
        source: ModuleType | type,
        dest: ModuleType | SubConfigProxy,
        prefix: str,
    ) -> None:
        """Walk the module structure and move everything to module._config"""
        type_hints = inspect.get_annotations(source)
        for key, value in list(source.__dict__.items()):
            if (
                key.startswith("__")
                or isinstance(value, (ModuleType, FunctionType))
                or (
                    hasattr(value, "__module__")
                    and (
                        value.__module__ == "typing"
                        or value.__module__.startswith("collections.abc")
                    )
                )
                # Handle from torch.utils._config_module import Config
                or (isinstance(value, type) and issubclass(value, _Config))
            ):
                continue

            name = f"{prefix}{key}"
            annotated_type = type_hints.get(key, None)
            if isinstance(value, CONFIG_TYPES):
                config[name] = _ConfigEntry(
                    _Config(default=value, value_type=annotated_type), name
                )
                if dest is module:
                    delattr(module, key)
            elif isinstance(value, _Config):
                if annotated_type is not None and value.value_type is None:
                    value.value_type = annotated_type

                config[name] = _ConfigEntry(value, name)

                if dest is module:
                    delattr(module, key)
            elif isinstance(value, type):
                if value.__module__ != module.__name__:
                    raise AssertionError(
                        f"subconfig class {value} must be defined in module {module.__name__}"
                    )
                # a subconfig with `class Blah:` syntax
                proxy = SubConfigProxy(module, f"{name}.")
                visit(value, proxy, f"{name}.")
                if dest is module:
                    setattr(dest, key, proxy)
                else:
                    dest.__dict__[key] = proxy
            else:
                raise AssertionError(f"Unhandled config {key}={value} ({type(value)})")