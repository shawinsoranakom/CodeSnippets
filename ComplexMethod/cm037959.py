def _try_resolve_transformers(
        self,
        architecture: str,
        model_config: ModelConfig,
    ) -> str | None:
        if architecture in _TRANSFORMERS_BACKEND_MODELS:
            return architecture

        auto_map: dict[str, str] = (
            getattr(model_config.hf_config, "auto_map", None) or dict()
        )

        # Make sure that config class is always initialized before model class,
        # otherwise the model class won't be able to access the config class,
        # the expected auto_map should have correct order like:
        # "auto_map": {
        #     "AutoConfig": "<your-repo-name>--<config-name>",
        #     "AutoModel": "<your-repo-name>--<config-name>",
        #     "AutoModelFor<Task>": "<your-repo-name>--<config-name>",
        # },
        for prefix in ("AutoConfig", "AutoModel"):
            for name, module in auto_map.items():
                if name.startswith(prefix):
                    try_get_class_from_dynamic_module(
                        module,
                        model_config.model,
                        revision=model_config.revision,
                        trust_remote_code=model_config.trust_remote_code,
                        warn_on_fail=False,
                    )

        model_module = getattr(transformers, architecture, None)

        if model_module is None:
            for name, module in auto_map.items():
                if name.startswith("AutoModel"):
                    model_module = try_get_class_from_dynamic_module(
                        module,
                        model_config.model,
                        revision=model_config.revision,
                        trust_remote_code=model_config.trust_remote_code,
                        warn_on_fail=True,
                    )
                    if model_module is not None:
                        break
            else:
                if model_config.model_impl != "transformers":
                    return None

                raise ValueError(
                    f"Cannot find model module. {architecture!r} is not a "
                    "registered model in the Transformers library (only "
                    "relevant if the model is meant to be in Transformers) "
                    "and 'AutoModel' is not present in the model config's "
                    "'auto_map' (relevant if the model is custom)."
                )

        if not model_module.is_backend_compatible():
            if model_config.model_impl != "transformers":
                return None

            raise ValueError(
                f"The Transformers implementation of {architecture!r} "
                "is not compatible with vLLM."
            )

        return model_config._get_transformers_backend_cls()