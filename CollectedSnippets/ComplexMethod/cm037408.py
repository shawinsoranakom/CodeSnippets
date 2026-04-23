def init_attn_backend(
    kv_cache_config: KVCacheConfig,
    vllm_config: VllmConfig,
    device: torch.device,
    active_layer_names: set[str] | None = None,
) -> tuple[
    dict[str, type[AttentionBackend]],
    list[list[AttentionGroup]],
    AttentionCGSupportInfo,
]:
    attn_backends: dict[str, type[AttentionBackend]] = {}
    attn_groups: list[list[AttentionGroup]] = []
    attn_backend_workspace: torch.Tensor | None = None
    # Find minimum cudagraph support across all attention backends
    min_cg_support = AttentionCGSupport.ALWAYS
    min_cg_attn_backend = None
    for kv_cache_group_id, kv_cache_group_spec in enumerate(
        kv_cache_config.kv_cache_groups
    ):
        layer_names = kv_cache_group_spec.layer_names
        if active_layer_names is not None:
            layer_names = list(active_layer_names.intersection(layer_names))

        layer_type = cast(type[Any], AttentionLayerBase)
        attn_layers = get_layers_from_vllm_config(vllm_config, layer_type, layer_names)

        group_map: dict[tuple[tuple[str, str], KVCacheSpec], AttentionGroup] = {}
        group_order: list[tuple[tuple[str, str], KVCacheSpec]] = []

        for layer_name in layer_names:
            attn_backend = attn_layers[layer_name].get_attn_backend()
            attn_backends[layer_name] = attn_backend

            layer_kv_cache_spec: KVCacheSpec = kv_cache_group_spec.kv_cache_spec
            if isinstance(layer_kv_cache_spec, UniformTypeKVCacheSpecs):
                layer_kv_cache_spec = layer_kv_cache_spec.kv_cache_specs[layer_name]

            key = (attn_backend.full_cls_name(), layer_kv_cache_spec)
            if key not in group_map:
                group_map[key] = AttentionGroup(
                    attn_backend,
                    [layer_name],
                    layer_kv_cache_spec,
                    kv_cache_group_id,
                )
                group_order.append(key)
            else:
                group_map[key].layer_names.append(layer_name)

        groups = [group_map[key] for key in group_order]
        for group in groups:
            group.create_metadata_builders(
                vllm_config=vllm_config,
                device=device,
                kernel_block_size=None,
                num_metadata_builders=1,
            )
            builder = group.get_metadata_builder(0)
            if attn_backend_workspace is None:
                if hasattr(builder, "_get_workspace_buffer"):
                    attn_backend_workspace = builder._get_workspace_buffer()
            else:
                if hasattr(builder, "set_workspace_buffer"):
                    builder.set_workspace_buffer(attn_backend_workspace)
            # Check cudagraph support for the attention backend
            cg_support = builder.get_cudagraph_support(
                vllm_config,
                cast(AttentionSpec, kv_cache_group_spec.kv_cache_spec),
            )
            if cg_support.value < min_cg_support.value:
                min_cg_support = cg_support
                min_cg_attn_backend = attn_backend.__name__
        attn_groups.append(groups)

    return (
        attn_backends,
        attn_groups,
        AttentionCGSupportInfo(
            min_cg_support=min_cg_support,
            min_cg_attn_backend=min_cg_attn_backend,
        ),
    )