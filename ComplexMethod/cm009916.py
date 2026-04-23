def with_config(
        self,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> _ConfigurableModel:
        """Bind config to a `Runnable`, returning a new `Runnable`."""
        config = RunnableConfig(**(config or {}), **cast("RunnableConfig", kwargs))
        model_params = self._model_params(config)
        remaining_config = {k: v for k, v in config.items() if k != "configurable"}
        remaining_config["configurable"] = {
            k: v
            for k, v in config.get("configurable", {}).items()
            if k.removeprefix(self._config_prefix) not in model_params
        }
        queued_declarative_operations = list(self._queued_declarative_operations)
        if remaining_config:
            queued_declarative_operations.append(
                (
                    "with_config",
                    (),
                    {"config": remaining_config},
                ),
            )
        return _ConfigurableModel(
            default_config={**self._default_config, **model_params},
            configurable_fields=list(self._configurable_fields)
            if isinstance(self._configurable_fields, list)
            else self._configurable_fields,
            config_prefix=self._config_prefix,
            queued_declarative_operations=queued_declarative_operations,
        )