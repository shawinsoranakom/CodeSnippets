def from_config(cls, config, **kwargs):
        trust_remote_code = kwargs.pop("trust_remote_code", None)
        has_remote_code = hasattr(config, "auto_map") and cls.__name__ in config.auto_map
        has_local_code = type(config) in cls._model_mapping
        explicit_local_code = has_local_code and not _get_model_class(
            config, cls._model_mapping
        ).__module__.startswith("transformers.")
        if has_remote_code:
            class_ref = config.auto_map[cls.__name__]
            if "--" in class_ref:
                upstream_repo = class_ref.split("--")[0]
            else:
                upstream_repo = None
            trust_remote_code = resolve_trust_remote_code(
                trust_remote_code, config._name_or_path, has_local_code, has_remote_code, upstream_repo=upstream_repo
            )

        if has_remote_code and trust_remote_code and not explicit_local_code:
            if "--" in class_ref:
                repo_id, class_ref = class_ref.split("--")
            else:
                repo_id = config.name_or_path
            model_class = get_class_from_dynamic_module(class_ref, repo_id, **kwargs)
            # This block handles the case where the user is loading a model with `trust_remote_code=True`
            # but a library model exists with the same name. We don't want to override the autoclass
            # mappings in this case, or all future loads of that model will be the remote code model.
            if not has_local_code:
                cls.register(config.__class__, model_class, exist_ok=True)
                model_class.register_for_auto_class(auto_class=cls)
            _ = kwargs.pop("code_revision", None)
            model_class = add_generation_mixin_to_remote_model(model_class)
            return model_class._from_config(config, **kwargs)
        elif has_local_code:
            model_class = _get_model_class(config, cls._model_mapping)
            return model_class._from_config(config, **kwargs)

        raise ValueError(
            f"Unrecognized configuration class {config.__class__} for this kind of AutoModel: {cls.__name__}.\n"
            f"Model type should be one of {', '.join(c.__name__ for c in cls._model_mapping)}."
        )