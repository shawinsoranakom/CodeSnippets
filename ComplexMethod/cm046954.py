def _get_per_token_logps_and_entropies(
        self,
        model,
        input_ids,
        attention_mask,
        logits_to_keep,
        batch_size = None,
        compute_entropy = False,
        compute_efficient = False,
        *args,
        **kwargs,
    ):
        # All Unsloth code here in this function is licensed under AGPL3
        # if True: # os.environ.get('UNSLOTH_USE_NEW_MODEL', '0') == '0':
        #     return None, None  # logps, entropies Unsloth efficient GRPO
        if compute_efficient:
            return None, None
        else:
            if not hasattr(self, "_autocast_dtype"):
                self._autocast_dtype = (
                    torch.float16
                    if os.environ.get("ACCELERATE_MIXED_PRECISION", "fp16") == "fp16"
                    else torch.bfloat16
                )
                if os.environ.get("UNSLOTH_FORCE_FLOAT32", "0") == "1":
                    self._autocast_dtype = torch.float16

            pixel_values, image_grid_thw = (
                kwargs.get("pixel_values", None),
                kwargs.get("image_grid_thw", None),
            )
            pixel_attention_mask, image_sizes = (
                kwargs.get("pixel_attention_mask", None),
                kwargs.get("image_sizes", None),
            )
            # Transformers 5.x needs token_type_ids/mm_token_type_ids for some vision models
            token_type_ids = kwargs.get("token_type_ids", None)
            mm_token_type_ids = kwargs.get("mm_token_type_ids", None)

            unwrapped_model = self.accelerator.unwrap_model(
                model, keep_fp32_wrapper = False
            )

            lm_head = self.model.get_output_embeddings().weight

            dtype_bytes = (
                16 if self._autocast_dtype in [torch.float16, torch.bfloat16] else 32
            )
            total_rows = input_ids.shape[0]
            seq_len = input_ids.shape[1]
            hidden_dim = lm_head.shape[1]
            vocab_dim = lm_head.shape[0]

            if self.args.unsloth_grpo_mini_batch is None:
                B, multiplier = autotune_batch_and_chunks(
                    total_rows,
                    seq_len,
                    hidden_dim,
                    vocab_dim,
                    dtype_bytes,
                    self.args.unsloth_logit_chunk_multiplier,
                )
                B = total_rows // B
            else:
                B = self.args.unsloth_grpo_mini_batch

                if self.args.unsloth_logit_chunk_multiplier is None:
                    multiplier = max(4, seq_len // 4096)
                else:
                    multiplier = self.args.unsloth_logit_chunk_multiplier

            all_logprobs_list = []
            if pixel_values is None:
                left_pad_tokens_per_prompt = calculate_pad_tokens_in_prompt(
                    input_ids, logits_to_keep, self.processing_class.pad_token_id
                )
                max_left_pad = torch.max(left_pad_tokens_per_prompt).item()
                input_ids = left_pack_padding(
                    input_ids, self.processing_class.pad_token_id
                )
                attention_mask = input_ids != self.processing_class.pad_token_id
                attention_mask = attention_mask.to(attention_mask.dtype)
            else:
                max_left_pad = 0

            # input_ids_chunks = torch.chunk(input_ids, chunks = B, dim = 0)
            attention_mask_chunks = torch.chunk(attention_mask, chunks = B, dim = 0)

            def chunk_optional(tensor, chunks):
                if tensor is None:
                    return [None] * chunks
                return torch.chunk(tensor, chunks = chunks, dim = 0)

            import math

            total_samples = input_ids.shape[0]
            batch_size = math.ceil(total_samples / B)

            input_ids_chunks = []
            attention_mask_chunks = []
            pixel_values_chunks = []
            image_grid_thw_chunks = []
            pixel_attention_mask_chunks = []

            current_pixel_idx = 0
            # TRL 0.23.0 batching logic
            for start in range(0, total_samples, batch_size):
                end = start + batch_size

                input_ids_chunks.append(input_ids[start:end])
                attention_mask_chunks.append(attention_mask[start:end])

                if image_grid_thw is not None and pixel_values is not None:
                    grid_slice = image_grid_thw[start:end]
                    image_grid_thw_chunks.append(grid_slice)

                    batch_pixel_count = grid_slice.prod(dim = -1).sum().item()

                    start_pixel_idx = current_pixel_idx
                    end_pixel_idx = current_pixel_idx + batch_pixel_count

                    pixel_values_chunks.append(
                        pixel_values[start_pixel_idx:end_pixel_idx]
                    )

                    if pixel_attention_mask is not None:
                        pixel_attention_mask_chunks.append(
                            pixel_attention_mask[start_pixel_idx:end_pixel_idx]
                        )
                    else:
                        pixel_attention_mask_chunks.append(None)

                    current_pixel_idx = end_pixel_idx

                else:
                    pixel_values_chunks.append(None)
                    image_grid_thw_chunks.append(None)
                    pixel_attention_mask_chunks.append(None)

            if image_sizes is not None and not isinstance(image_sizes, torch.Tensor):
                image_sizes_chunks = [[size] for size in image_sizes]
            else:
                image_sizes_chunks = chunk_optional(image_sizes, B)

            temperature = self.temperature
            logit_softcapping = _unsloth_get_final_logit_softcapping(model.config)
            logit_scale_multiply = getattr(model.config, "logit_scale", 0)
            if logit_scale_multiply is None:
                logit_scale_multiply = 0
            logit_scale_divide = getattr(model.config, "logits_scaling", 0)
            if logit_scale_divide is None:
                logit_scale_divide = 0

            # Transformers 5.x needs token_type_ids/mm_token_type_ids for some vision models
            token_type_ids_chunks = chunk_optional(token_type_ids, B)
            mm_token_type_ids_chunks = chunk_optional(mm_token_type_ids, B)

            zipped_inputs = zip(
                input_ids_chunks,
                attention_mask_chunks,
                pixel_values_chunks,
                image_grid_thw_chunks,
                pixel_attention_mask_chunks,
                image_sizes_chunks,
                token_type_ids_chunks,
                mm_token_type_ids_chunks,
            )
            os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "1"

            with _get_inference_mode_context_manager(model):
                for (
                    input_ids_chunk,
                    attention_mask_chunk,
                    pixel_values_chunk,
                    image_grid_thw_chunk,
                    pixel_attention_mask_chunk,
                    image_sizes_chunk,
                    token_type_ids_chunk,
                    mm_token_type_ids_chunk,
                ) in zipped_inputs:
                    _extra_vision_kwargs = {}
                    if token_type_ids_chunk is not None:
                        _extra_vision_kwargs["token_type_ids"] = token_type_ids_chunk
                    if mm_token_type_ids_chunk is not None:
                        _extra_vision_kwargs["mm_token_type_ids"] = (
                            mm_token_type_ids_chunk
                        )
                    with torch.amp.autocast(
                        device_type = "cuda", dtype = self._autocast_dtype
                    ):
                        if pixel_values is None:
                            logits_chunk = unwrapped_model(
                                input_ids = input_ids_chunk,
                                attention_mask = attention_mask_chunk,
                                pixel_values = pixel_values_chunk,
                                image_grid_thw = image_grid_thw_chunk,
                                pixel_attention_mask = pixel_attention_mask_chunk,
                                image_sizes = image_sizes_chunk,
                                **_extra_vision_kwargs,
                            ).logits

                            completion_input_ids_chunk = input_ids_chunk[
                                :, -(logits_to_keep + max_left_pad) :
                            ]
                            logits_chunk = logits_chunk[
                                :, -(logits_to_keep + max_left_pad + 1) :, :
                            ]
                            logits_chunk = logits_chunk[:, :-1, :]
                            logprobs_chunk = (
                                chunked_hidden_states_selective_log_softmax(
                                    logits_chunk,
                                    lm_head,
                                    completion_input_ids_chunk,
                                    chunks = input_ids_chunk.shape[0] * multiplier,
                                    logit_scale_multiply = logit_scale_multiply,
                                    logit_scale_divide = logit_scale_divide,
                                    logit_softcapping = logit_softcapping,
                                    temperature = temperature,
                                )
                            )
                        else:
                            # Essentially, for VLMs we do not go via the optimized path in models/,
                            # so we don't encounter the Flash Attn left-padding issue.
                            logits_chunk = unwrapped_model(
                                input_ids = input_ids_chunk,
                                attention_mask = attention_mask_chunk,
                                pixel_values = pixel_values_chunk,
                                image_grid_thw = image_grid_thw_chunk,
                                pixel_attention_mask = pixel_attention_mask_chunk,
                                image_sizes = image_sizes_chunk,
                                logits_to_keep = logits_to_keep + 1,
                                **_extra_vision_kwargs,
                            ).logits

                            logits_chunk = logits_chunk[:, :-1, :]
                            completion_input_ids_chunk = input_ids_chunk[
                                :, -logits_to_keep:
                            ]
                            # Guard: check if model returned hidden states or logits
                            if logits_chunk.shape[-1] == lm_head.shape[1]:
                                logprobs_chunk = (
                                    chunked_hidden_states_selective_log_softmax(
                                        logits_chunk,
                                        lm_head,
                                        completion_input_ids_chunk,
                                        chunks = input_ids_chunk.shape[0] * multiplier,
                                        logit_scale_multiply = logit_scale_multiply,
                                        logit_scale_divide = logit_scale_divide,
                                        logit_softcapping = logit_softcapping,
                                        temperature = temperature,
                                    )
                                )
                            else:
                                # Model returned logits directly - scaling/softcapping already applied by model forward
                                logprobs_chunk = chunked_selective_log_softmax(
                                    logits_chunk,
                                    completion_input_ids_chunk,
                                    temperature,
                                )
                    # This is needed to avoid race conditions with GPT OSS offload_embbed=True
                    # However, it seems that this line does not slow down or disrupt models.
                    device_synchronize()
                    all_logprobs_list.append(logprobs_chunk)
                logprobs = torch.cat(all_logprobs_list, dim = 0)
                entropies = None

            os.environ["UNSLOTH_RETURN_HIDDEN_STATES"] = "0"

            return logprobs.detach(), entropies