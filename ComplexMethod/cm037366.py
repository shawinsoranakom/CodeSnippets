def _execute_mm_encoder(
        self, scheduler_output: "SchedulerOutput"
    ) -> list[torch.Tensor]:
        mm_hashes, mm_kwargs, mm_lora_refs = self._batch_mm_inputs_from_scheduler(
            scheduler_output
        )

        if not mm_kwargs:
            return []

        should_time = bool(
            self.observability_config
            and self.observability_config.enable_mm_processor_stats
            and scheduler_output.scheduled_encoder_inputs
        )

        # Batch mm inputs as much as we can: if a request in the batch has
        # multiple modalities or a different modality than the previous one,
        # we process it separately to preserve item order.
        # FIXME(ywang96): This is a hacky way to deal with multiple modalities
        # in the same batch while still being able to benefit from batching
        # multimodal inputs. The proper solution should be reordering the
        # encoder outputs.
        model = cast(SupportsMultiModal, self.model)

        if self.lora_config and self.lora_manager.supports_tower_connector_lora():
            # Build LoRA mappings independently for encoder inputs
            # (encoder batch structure is different from main batch)
            prompt_lora_mapping = []
            token_lora_mapping = []
            lora_requests = set()
            encoder_token_counts = []

            for req_id, pos_info in mm_lora_refs:
                req_idx = self.input_batch.req_id_to_index[req_id]
                lora_id = int(self.input_batch.request_lora_mapping[req_idx])

                # Prefer pos_info.get_num_embeds to count precise MM embedding tokens.
                num_tokens = self.model.get_num_mm_encoder_tokens(  # type: ignore[attr-defined]
                    pos_info.get_num_embeds()
                )
                prompt_lora_mapping.append(lora_id)
                token_lora_mapping.extend([lora_id] * num_tokens)
                encoder_token_counts.append(num_tokens)

                if lora_id > 0:
                    lora_request = self.input_batch.lora_id_to_lora_request.get(lora_id)
                    if lora_request is not None:
                        lora_requests.add(lora_request)

            # Set tower adapter mapping
            tower_mapping = LoRAMapping(
                tuple(token_lora_mapping),
                tuple(prompt_lora_mapping),
                is_prefill=True,
                type=LoRAMappingType.TOWER,
            )
            self.lora_manager.set_active_adapters(lora_requests, tower_mapping)

            # Only set connector mapping if the model actually has a connector.
            # Some multimodal models inherit a stub `get_num_mm_connector_tokens`
            # from `SupportsMultiModal`, which returns None and should not be
            # treated as a signal that connector LoRA is supported.
            mm_mapping = (
                self.model.get_mm_mapping()  # type: ignore[attr-defined]
                if hasattr(self.model, "get_mm_mapping")
                else None
            )
            if (
                mm_mapping is not None
                and mm_mapping.connector
                and hasattr(self.model, "get_num_mm_connector_tokens")
            ):
                post_op_counts = [
                    self.model.get_num_mm_connector_tokens(num_tokens)  # type: ignore[attr-defined]
                    for num_tokens in encoder_token_counts
                ]

                connector_token_mapping = np.repeat(
                    np.array(prompt_lora_mapping, dtype=np.int32),
                    np.array(post_op_counts, dtype=np.int32),
                )
                connector_mapping = LoRAMapping(
                    index_mapping=tuple(connector_token_mapping.tolist()),
                    prompt_mapping=tuple(prompt_lora_mapping),
                    is_prefill=True,
                    type=LoRAMappingType.CONNECTOR,
                )

                self.lora_manager.set_active_adapters(
                    lora_requests,
                    connector_mapping,
                )

        encoder_outputs: list[torch.Tensor] = []
        # Track the current index in mm_kwargs/mm_lora_refs to map groups to request IDs
        current_item_idx = 0
        for modality, num_items, mm_kwargs_batch in group_and_batch_mm_kwargs(
            mm_kwargs,
            device=self.device,
            pin_memory=self.pin_memory,
        ):
            batch_outputs: MultiModalEmbeddings

            # EVS and dynamic res video related change.
            # (ekhvedchenia): Temporary hack to limit peak memory usage when
            # processing multimodal data. This solves the issue with scheduler
            # putting too many video samples into a single batch. Scheduler
            # uses pruned vision tokens count to compare it versus compute
            # budget which is incorrect (Either input media size or non-pruned
            # output vision tokens count should be considered)
            # dynamic res video for nemotron temporarily uses this hack via
            # requires_sequential_video_encoding
            # because it doesn't yet support video batching.
            # TODO(ywang96): Fix memory profiling to take EVS into account and
            # remove this hack.
            if (
                (
                    self.is_multimodal_pruning_enabled
                    or self.requires_sequential_video_encoding
                )
                and modality == "video"
                and num_items > 1
            ):
                batch_outputs_lst = list[torch.Tensor]()
                for video_idx in range(num_items):
                    video_mm_kwargs_item = mm_kwargs[current_item_idx + video_idx]
                    with self.timed_encoder_operation(
                        should_time, mm_lora_refs, current_item_idx + video_idx, 1
                    ):
                        _, _, micro_batch_mm_inputs = next(
                            group_and_batch_mm_kwargs(
                                [video_mm_kwargs_item],
                                device=self.device,
                                pin_memory=self.pin_memory,
                            )
                        )

                        micro_batch_outputs = model.embed_multimodal(
                            **micro_batch_mm_inputs
                        )

                        batch_outputs_lst.extend(micro_batch_outputs)

                batch_outputs = batch_outputs_lst
            else:
                # Run the encoder.
                # `batch_outputs` is either of the following:
                # 1. A tensor of shape (num_items, feature_size, hidden_size)
                # in case feature_size is fixed across all multimodal items.
                # 2. A list or tuple (length: num_items) of tensors,
                # each of shape (feature_size, hidden_size) in case the feature
                # size is dynamic depending on the input multimodal items.

                with self.timed_encoder_operation(
                    should_time, mm_lora_refs, current_item_idx, num_items
                ):
                    cudagraph_output = None
                    if (
                        self.encoder_cudagraph_manager is not None
                        and self.encoder_cudagraph_manager.supports_modality(modality)
                    ):
                        cudagraph_output = self.encoder_cudagraph_manager.execute(
                            mm_kwargs_batch,
                        )

                    if cudagraph_output is not None:
                        batch_outputs = cudagraph_output
                    else:
                        batch_outputs = model.embed_multimodal(**mm_kwargs_batch)

            sanity_check_mm_encoder_outputs(batch_outputs, expected_num_items=num_items)
            encoder_outputs.extend(batch_outputs)

            current_item_idx += num_items

        # Cache the encoder outputs by mm_hash
        for mm_hash, output in zip(mm_hashes, encoder_outputs):
            self.encoder_cache[mm_hash] = output
            logger.debug("Finish execute for mm hash %s", mm_hash)
            self.maybe_save_ec_to_connector(self.encoder_cache, mm_hash)

        return encoder_outputs