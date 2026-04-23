def allocate_uniform_kv_caches(
        kv_cache_config: KVCacheConfig,
        attn_groups: list[list[AttentionGroup]],
        cache_dtype: CacheDType,
        device: torch.device,
        kernel_block_sizes: list[int],
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor, type[AttentionBackend]]:
        """
        Initializes and reshapes KV caches for the simple case where all
        layers have the same layout.

        This function assumes use_uniform_kv_cache() returned True.

        Args:
            kv_cache_config: The KV cache config
            attn_groups: The list of attention groups for this model
            cache_dtype: The KV cache dtype
            device: The torch device to allocate on.
            kernel_block_sizes: The kernel block sizes for each KV cache group.
        Returns:
            A tuple (kv_caches, cross_layers_kv_cache, attn_backend) where:
                kv_caches is a dict mapping between layer names to their
                    corresponding memory buffer for KV cache.
                cross_layers_kv_cache is the cross layers kv cache tensor
                attn_backend is the attention backend matching this tensor
        """
        attn_group = attn_groups[0][0]
        kv_cache_spec = attn_group.kv_cache_spec
        assert isinstance(kv_cache_spec, AttentionSpec)

        tensor_sizes = set(
            kv_cache_tensor.size for kv_cache_tensor in kv_cache_config.kv_cache_tensors
        )
        assert len(tensor_sizes) == 1
        tensor_size = tensor_sizes.pop()

        page_size = kv_cache_spec.page_size_bytes
        assert tensor_size % page_size == 0
        num_blocks = tensor_size // page_size
        num_layers = len(kv_cache_config.kv_cache_tensors)
        total_size = tensor_size * num_layers

        assert len(kernel_block_sizes) == 1
        kernel_block_size = kernel_block_sizes[0]
        num_blocks_per_kv_block = kv_cache_spec.block_size // kernel_block_size
        kernel_num_blocks = num_blocks * num_blocks_per_kv_block

        attn_backend = attn_group.backend
        kv_cache_shape = attn_backend.get_kv_cache_shape(
            kernel_num_blocks,
            kernel_block_size,
            kv_cache_spec.num_kv_heads,
            kv_cache_spec.head_size,
            cache_dtype_str=cache_dtype,
        )

        # prepend a num_layers dimension into the shape
        kv_cache_shape = (num_layers,) + kv_cache_shape

        try:
            kv_cache_stride_order = attn_backend.get_kv_cache_stride_order(
                include_num_layers_dimension=True
            )
            assert len(kv_cache_stride_order) == len(kv_cache_shape)
        except (AttributeError, NotImplementedError):
            kv_cache_stride_order = tuple(range(len(kv_cache_shape)))

        kv_cache_shape = tuple(kv_cache_shape[i] for i in kv_cache_stride_order)

        logger.info("Allocating a cross layer KV cache of shape %s", kv_cache_shape)

        # allocate one contiguous buffer for all layers
        cross_layers_kv_cache = (
            torch.zeros(total_size, dtype=torch.int8, device=device)
            .view(kv_cache_spec.dtype)
            .view(kv_cache_shape)
        )

        # Maintain original KV shape view.
        inv_order = [
            kv_cache_stride_order.index(i) for i in range(len(kv_cache_stride_order))
        ]
        permuted_kv_cache = cross_layers_kv_cache.permute(*inv_order)

        kv_caches = {}
        for i, kv_cache_tensor in enumerate(kv_cache_config.kv_cache_tensors):
            tensor = permuted_kv_cache[i]
            for layer_name in kv_cache_tensor.shared_by:
                kv_caches[layer_name] = tensor

        return kv_caches, cross_layers_kv_cache, attn_backend