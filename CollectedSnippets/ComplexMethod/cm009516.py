def _prepare(
        self, config: RunnableConfig | None = None
    ) -> tuple[Runnable[Input, Output], RunnableConfig]:
        config = ensure_config(config)
        specs_by_id = {spec.id: (key, spec) for key, spec in self.fields.items()}
        configurable_fields = {
            specs_by_id[k][0]: v
            for k, v in config.get("configurable", {}).items()
            if k in specs_by_id and isinstance(specs_by_id[k][1], ConfigurableField)
        }
        configurable_single_options = {
            k: v.options[(config.get("configurable", {}).get(v.id) or v.default)]
            for k, v in self.fields.items()
            if isinstance(v, ConfigurableFieldSingleOption)
        }
        configurable_multi_options = {
            k: [
                v.options[o]
                for o in config.get("configurable", {}).get(v.id, v.default)
            ]
            for k, v in self.fields.items()
            if isinstance(v, ConfigurableFieldMultiOption)
        }
        configurable = {
            **configurable_fields,
            **configurable_single_options,
            **configurable_multi_options,
        }

        if configurable:
            init_params = {
                k: v
                for k, v in self.default.__dict__.items()
                if k in type(self.default).model_fields
            }
            return (
                self.default.__class__(**{**init_params, **configurable}),
                config,
            )
        return (self.default, config)