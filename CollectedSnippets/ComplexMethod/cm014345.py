def __init__(self, config: _Config, name: str) -> None:
        self.default = config.default
        self.value_type = (
            config.value_type if config.value_type is not None else type(self.default)
        )
        self.justknob = config.justknob
        self.alias = config.alias
        # Deprecation fields
        self.deprecated = config.deprecated
        self.deprecation_message = config.deprecation_message
        self._deprecation_warned = False

        self.user_override = ContextVar(name, default=_UNSET_SENTINEL)
        if config.env_name_default is not None:
            for val in config.env_name_default:
                if (env_value := _read_env_variable(val)) is not None:
                    self.env_value_default = env_value
                    break
        if config.env_name_force is not None:
            for val in config.env_name_force:
                if (env_value := _read_env_variable(val)) is not None:
                    self.env_value_force = env_value
                    break

        # Ensure justknobs and envvars are allowlisted types
        if self.justknob is not None and self.default is not None:
            if not isinstance(self.default, bool):
                raise AssertionError(
                    f"justknobs only support booleans, {self.default} is not a boolean"
                )
        if self.value_type is not None and (
            config.env_name_default is not None or config.env_name_force is not None
        ):
            if self.value_type not in (
                bool,
                str,
                Optional[bool],  # noqa: UP045
                Optional[str],  # noqa: UP045
            ):
                raise AssertionError(
                    f"envvar configs only support (optional) booleans or strings, {self.value_type} is neither"
                )