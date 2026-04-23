def consolidate_backbone_kwargs_to_config(
    backbone_config,
    default_backbone: str | None = None,
    default_config_type: str | None = None,
    default_config_kwargs: dict | None = None,
    timm_default_kwargs: dict | None = None,
    **kwargs,
):
    # Lazy import to avoid circular import issues. Can be imported properly
    # after deleting ref to `BackboneMixin` in `utils/backbone_utils.py`
    from .configuration_utils import PreTrainedConfig
    from .models.auto import CONFIG_MAPPING

    use_timm_backbone = kwargs.pop("use_timm_backbone", True)
    backbone_kwargs = kwargs.pop("backbone_kwargs", {})
    backbone = kwargs.pop("backbone") if kwargs.get("backbone") is not None else default_backbone
    kwargs.pop("use_pretrained_backbone", None)

    # Init timm backbone with hardcoded values for BC. If everything is set to `None` and there is
    # a default timm config, we use it to init the backbone.
    if (
        timm_default_kwargs is not None
        and use_timm_backbone
        and backbone is not None
        and backbone_config is None
        and not backbone_kwargs
    ):
        backbone_config = CONFIG_MAPPING["timm_backbone"](backbone=backbone, **timm_default_kwargs)
    elif backbone is not None and backbone_config is None:
        if repo_exists(backbone):
            config_dict, _ = PreTrainedConfig.get_config_dict(backbone)
            config_class = CONFIG_MAPPING[config_dict["model_type"]]
            config_dict.update(backbone_kwargs)
            backbone_config = config_class(**config_dict)
        else:
            backbone_config = CONFIG_MAPPING["timm_backbone"](backbone=backbone, **backbone_kwargs)
    elif backbone_config is None and default_config_type is not None:
        logger.info(
            f"`backbone_config` is `None`. Initializing the config with the default `{default_config_type}` vision config."
        )
        default_config_kwargs = default_config_kwargs or {}
        backbone_config = CONFIG_MAPPING[default_config_type](**default_config_kwargs)
    elif isinstance(backbone_config, dict):
        backbone_model_type = backbone_config.get("model_type")
        config_class = CONFIG_MAPPING[backbone_model_type]
        backbone_config = config_class.from_dict(backbone_config)

    return backbone_config, kwargs