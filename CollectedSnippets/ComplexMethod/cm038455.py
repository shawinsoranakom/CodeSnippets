def start_load_kv(self, forward_context: "ForwardContext", **kwargs: Any) -> None:
        """Start loading the KV cache from the connector buffer to vLLM's
        paged KV buffer.

        Args:
            forward_context (ForwardContext): the forward context.
            **kwargs: additional arguments for the load operation

        Note:
            The number of elements in kv_caches and layer_names should be
            the same.
        """

        def inject_kv_into_layer(
            dst_kv_cache_layer: torch.Tensor,
            src_kv_cache: torch.Tensor,
            slot_mapping: torch.Tensor,
            attn_metadata: AttentionMetadata,
        ) -> None:
            """Inject the KV cache into the layer.

            Args:
                dst_kv_cache_layer (torch.Tensor): the destination KV cache
                    layer. In shape [2, num_pages, page_size, xxx] if not
                    using MLA, [num_pages, page_size, xxx] otherwise.
                src_kv_cache (torch.Tensor): the source KV cache. In shape
                    [2, num_tokens, xxx] if not using MLA, [num_tokens, xxx]
                    otherwise.
                slot_mapping (torch.Tensor): the slot mapping. In shape
                    [num_tokens].
            """
            dst_kv_cache_layer_shape = dst_kv_cache_layer.shape
            if isinstance(attn_metadata, MLACommonMetadata):
                num_pages = dst_kv_cache_layer_shape[0]
                page_size = dst_kv_cache_layer_shape[1]
                dst_kv_cache_layer = dst_kv_cache_layer.reshape(
                    num_pages * page_size, -1
                )
                dst_kv_cache_layer[slot_mapping, ...] = src_kv_cache
            elif isinstance(attn_metadata, TritonAttentionMetadata):
                block_idxs = slot_mapping // self._block_size
                offsets = slot_mapping % self._block_size
                dst_kv_cache_layer[block_idxs, :, offsets] = src_kv_cache
            else:
                num_pages = dst_kv_cache_layer_shape[1]
                page_size = dst_kv_cache_layer_shape[2]
                dst_kv_cache_layer = dst_kv_cache_layer.reshape(
                    2, num_pages * page_size, -1
                )
                dst_kv_cache_layer[:, slot_mapping, ...] = src_kv_cache

        # Get the metadata
        metadata: KVConnectorMetadata = self._get_connector_metadata()
        assert isinstance(metadata, ExampleConnectorMetadata)

        attn_metadata = forward_context.attn_metadata
        if attn_metadata is None:
            logger.warning("In connector.start_load_kv, but the attn_metadata is None")
            return

        # Load the KV for each request each layer
        for request in metadata.requests:
            if request.is_store:
                continue
            logger.info(
                "Inject KV cache of %d tokens to the paged memory",
                len(request.slot_mapping),
            )
            for layer_name in forward_context.no_compile_layers:
                layer = forward_context.no_compile_layers[layer_name]

                # Only process layers that have kv_cache
                # attribute (attention layers) Skip non-attention
                # layers like FusedMoE/MLP etc.
                kv_cache_layer = getattr(layer, "kv_cache", None)
                if kv_cache_layer is None:
                    continue

                filename = self._generate_filename_debug(
                    layer_name, request.token_ids, request.mm_hashes
                )
                kv_cache = safetensors.torch.load_file(filename)["kv_cache"].cuda()
                if isinstance(attn_metadata, dict):
                    inject_kv_into_layer(
                        kv_cache_layer,
                        kv_cache,
                        request.slot_mapping,
                        attn_metadata[layer_name],
                    )