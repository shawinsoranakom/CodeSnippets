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

        # Only consumer/decode loads KV Cache
        if self.is_producer:
            return

        assert self.p2p_nccl_engine is not None

        attn_metadata = forward_context.attn_metadata
        if attn_metadata is None:
            return

        def inject_kv_into_layer(
            layer: torch.Tensor,
            kv_cache: torch.Tensor,
            block_ids: torch.Tensor,
            request_id: str,
        ) -> None:
            """
            Inject KV cache data into a given attention layer tensor.

            This function updates `layer` in-place with values from `kv_cache`,
            handling different backend layouts:
              - MLA (Multi-Linear Attention) or FlashInfer: KV tensors are
                indexed along the first dimension.
              - FlashAttention: KV tensors are indexed along the second
                dimension.

            If the number of provided block IDs does not match the number of KV
            blocks, only the overlapping portion is updated, and a warning is
            logged.

            Args:
                layer (torch.Tensor): The attention layer KV tensor to update.
                kv_cache (torch.Tensor): The KV cache tensor to inject.
                block_ids (torch.Tensor): Indices of the blocks to update.
                request_id (str): Request identifier used for logging.

            Returns:
                None. The function modifies `layer` in-place.
            """
            if (
                isinstance(attn_metadata, MLACommonMetadata) or layer.shape[1] == 2
            ):  # MLA or FlashInfer
                num_block = kv_cache.shape[0]
                self.check_tensors_except_dim(layer, kv_cache, 0)
                if len(block_ids) == num_block:
                    layer[block_ids, ...] = kv_cache
                else:
                    layer[block_ids[:num_block], ...] = kv_cache
                    logger.warning(
                        "🚧kv_cache does not match, block_ids:%d, "
                        "num_block:%d, request_id:%s",
                        len(block_ids),
                        num_block,
                        request_id,
                    )

            elif layer.shape[0] == 2:  # FlashAttention
                num_block = kv_cache.shape[1]
                self.check_tensors_except_dim(layer, kv_cache, 1)
                if len(block_ids) == num_block:
                    layer[:, block_ids, ...] = kv_cache
                else:
                    layer[:, block_ids[:num_block], ...] = kv_cache
                    logger.warning(
                        "🚧kv_cache does not match, block_ids:%d, "
                        "num_block:%d, request_id:%s",
                        len(block_ids),
                        num_block,
                        request_id,
                    )

        # Get the metadata
        metadata: KVConnectorMetadata = self._get_connector_metadata()
        assert isinstance(metadata, P2pNcclConnectorMetadata)

        if metadata is None:
            return

        # Load the KV for each request each layer
        for request in metadata.requests:
            request_id = request.request_id
            ip, port = self.parse_request_id(request_id, False)
            remote_address = ip + ":" + str(port + self._rank)
            for layer_name in forward_context.no_compile_layers:
                layer = forward_context.no_compile_layers[layer_name]

                # Only process layers that have kv_cache
                # attribute (attention layers) Skip non-attention
                # layers like FusedMoE
                kv_cache = getattr(layer, "kv_cache", None)
                if kv_cache is None:
                    continue

                layer = kv_cache

                kv_cache = self.p2p_nccl_engine.recv_tensor(
                    request.request_id + "#" + layer_name, remote_address
                )

                if kv_cache is None:
                    logger.warning("🚧kv_cache is None, %s", request.request_id)
                    continue

                inject_kv_into_layer(
                    layer, kv_cache, request.block_ids, request.request_id
                )