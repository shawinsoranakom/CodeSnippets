def _discover_fusable_modules(
    cls: "type[PreTrainedModel]",
    config: "PretrainedConfig",
    fusion_name: str,
    spec: ModuleFusionSpec,
) -> dict[str, type[nn.Module]]:
    """Discover compatible module classes for one fusion family on a meta-initialized model.

    This function:
    - instantiates `cls(config)` on the meta device
    - scans `named_modules()` for candidate modules
    - optionally pre-filters them with `target_modules_patterns`
    - uses `is_fusable(...)` as the final structural check
    - builds the class-level patch mapping used by monkey patching

    Results are cached per `(fusion_name, cls)` to avoid repeated meta-initialization.
    This matches the current class-level fusion behavior, where one compatible
    module class maps to one fused replacement class.
    """

    cache = _FUSION_DISCOVERY_CACHE.setdefault(fusion_name, {})
    if cls in cache:
        return cache[cls]

    with torch.device("meta"):
        model = cls(config)

    seen_classes = set()
    patch_mapping = {}
    target_module_pattern = (
        re.compile("|".join(spec.target_modules_patterns)) if spec.target_modules_patterns else None
    )
    for module_name, module in model.named_modules():
        module_cls = type(module)
        if module_cls in seen_classes:
            continue
        if target_module_pattern is not None and target_module_pattern.search(module_name) is None:
            continue
        if not spec.is_fusable(module):
            continue

        seen_classes.add(module_cls)
        patch_mapping[module_cls.__name__] = spec.make_fused_class(module_cls)

    cache[cls] = patch_mapping
    return patch_mapping