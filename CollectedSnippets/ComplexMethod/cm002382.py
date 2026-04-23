def _build_model_tester_and_get_config(tester_class, model_tester_kwargs, model_type):
    """Instantiate a model tester and retrieve a tiny config from it.

    Falls back to stripping `vocab_size` from kwargs on `TypeError`, to handle testers
    that don't accept it directly (e.g. multimodal testers using `text_kwargs`).
    """
    try:
        model_tester = tester_class(parent=None, **model_tester_kwargs)
    except TypeError:
        # Strip `vocab_size` from top-level kwargs and from any nested dict kwargs
        # (e.g. `config_kwargs` in `PeVideoTextModelTester`).
        model_tester_kwargs_new = {k: v for k, v in model_tester_kwargs.items() if k != "vocab_size"}
        for k, v in model_tester_kwargs_new.items():
            if isinstance(v, dict):
                model_tester_kwargs_new[k] = {k1: v1 for k1, v1 in v.items() if k1 != "vocab_size"}
        model_tester = tester_class(parent=None, **model_tester_kwargs_new)

    if hasattr(model_tester, "get_pipeline_config"):
        config = model_tester.get_pipeline_config()
    elif hasattr(model_tester, "prepare_config_and_inputs"):
        # `PoolFormer` has no `get_config` defined. Furthermore, it's better to use `prepare_config_and_inputs` even if
        # `get_config` is defined, since there might be some extra changes in `prepare_config_and_inputs`.
        # We don't really need to call `prepare_config_and_inputs` which might require more dependencies.
        if hasattr(model_tester, "get_config"):
            try:
                config = model_tester.prepare_config_and_inputs()[0]
            except Exception:
                config = model_tester.get_config()
        else:
            config = model_tester.prepare_config_and_inputs()[0]
    elif hasattr(model_tester, "get_config"):
        config = model_tester.get_config()
    else:
        raise ValueError(
            f"Tiny config not created for {model_type} - the model tester {tester_class.__name__} lacks"
            " a necessary method to create config."
        )

    return model_tester, config