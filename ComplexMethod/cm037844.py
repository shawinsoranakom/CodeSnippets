def _get_model_architecture(model_config: ModelConfig) -> tuple[type[nn.Module], str]:
    from vllm.model_executor.models.adapters import as_embedding_model, as_seq_cls_model

    architectures = getattr(model_config.hf_config, "architectures", None) or []

    model_cls, arch = model_config.registry.resolve_model_cls(
        architectures,
        model_config=model_config,
    )

    if arch == model_config._get_transformers_backend_cls():
        assert model_config.model_impl != "vllm"
        if model_config.model_impl == "auto":
            logger.warning_once(
                "%s has no vLLM implementation, falling back to Transformers "
                "implementation. Some features may not be supported and "
                "performance may not be optimal.",
                arch,
            )

    convert_type = model_config.convert_type
    if convert_type == "none":
        pass
    elif convert_type == "embed":
        logger.debug_once("Converting to embedding model.")
        model_cls = as_embedding_model(model_cls)
    elif convert_type == "classify":
        logger.debug_once("Converting to sequence classification model.")
        model_cls = as_seq_cls_model(model_cls)
    else:
        assert_never(convert_type)

    return model_cls, arch