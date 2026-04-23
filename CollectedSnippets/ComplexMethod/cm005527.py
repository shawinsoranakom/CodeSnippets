def generate(
        self: "GenerativePreTrainedModel",
        inputs: torch.Tensor | None = None,
        generation_config: GenerationConfig | None = None,
        logits_processor: LogitsProcessorList | None = None,
        stopping_criteria: StoppingCriteriaList | None = None,
        prefix_allowed_tokens_fn: Callable[[int, torch.Tensor], list[int]] | None = None,
        synced_gpus: bool | None = None,
        assistant_model: Optional["PreTrainedModel"] = None,
        streamer: Optional["BaseStreamer"] = None,
        negative_prompt_ids: torch.Tensor | None = None,
        negative_prompt_attention_mask: torch.Tensor | None = None,
        custom_generate: str | Callable | None = None,
        **kwargs,
    ) -> GenerateOutput | torch.LongTensor:
        r"""

        Generates sequences of token ids for models with a language modeling head.

        <Tip warning={true}>

        Most generation-controlling parameters are set in `generation_config` which, if not passed, will be set to the
        model's default generation configuration. You can override any `generation_config` by passing the corresponding
        parameters to generate(), e.g. `.generate(inputs, num_beams=4, do_sample=True)`.

        For an overview of generation strategies and code examples, check out the [following
        guide](../generation_strategies).

        </Tip>

        Parameters:
            inputs (`torch.Tensor` of varying shape depending on the modality, *optional*):
                The sequence used as a prompt for the generation or as model inputs to the encoder. If `None` the
                method initializes it with `bos_token_id` and a batch size of 1. For decoder-only models `inputs`
                should be in the format of `input_ids`. For encoder-decoder models *inputs* can represent any of
                `input_ids`, `input_values`, `input_features`, or `pixel_values`.
            generation_config ([`~generation.GenerationConfig`], *optional*):
                The generation configuration to be used as base parametrization for the generation call. `**kwargs`
                passed to generate matching the attributes of `generation_config` will override them. If
                `generation_config` is not provided, the default will be used, which has the following loading
                priority: 1) from the `generation_config.json` model file, if it exists; 2) from the model
                configuration. Please note that unspecified parameters will inherit [`~generation.GenerationConfig`]'s
                default values, whose documentation should be checked to parameterize generation.
            logits_processor (`LogitsProcessorList`, *optional*):
                Custom logits processors that complement the default logits processors built from arguments and
                generation config. If a logit processor is passed that is already created with the arguments or a
                generation config an error is thrown. This feature is intended for advanced users.
            stopping_criteria (`StoppingCriteriaList`, *optional*):
                Custom stopping criteria that complements the default stopping criteria built from arguments and a
                generation config. If a stopping criteria is passed that is already created with the arguments or a
                generation config an error is thrown. If your stopping criteria depends on the `scores` input, make
                sure you pass `return_dict_in_generate=True, output_scores=True` to `generate`. This feature is
                intended for advanced users.
            prefix_allowed_tokens_fn (`Callable[[int, torch.Tensor], list[int]]`, *optional*):
                If provided, this function constraints the beam search to allowed tokens only at each step. If not
                provided no constraint is applied. This function takes 2 arguments: the batch ID `batch_id` and
                `input_ids`. It has to return a list with the allowed tokens for the next generation step conditioned
                on the batch ID `batch_id` and the previously generated tokens `inputs_ids`. This argument is useful
                for constrained generation conditioned on the prefix, as described in [Autoregressive Entity
                Retrieval](https://huggingface.co/papers/2010.00904).
            synced_gpus (`bool`, *optional*):
                Whether to continue running the while loop until max_length. Unless overridden, this flag will be set
                to `True` if using `FullyShardedDataParallel` or DeepSpeed ZeRO Stage 3 with multiple GPUs to avoid
                deadlocking if one GPU finishes generating before other GPUs. Otherwise, defaults to `False`.
            assistant_model (`PreTrainedModel`, *optional*):
                An assistant model that can be used to accelerate generation. The assistant model must have the exact
                same tokenizer. The acceleration is achieved when forecasting candidate tokens with the assistant model
                is much faster than running generation with the model you're calling generate from. As such, the
                assistant model should be much smaller.
            streamer (`BaseStreamer`, *optional*):
                Streamer object that will be used to stream the generated sequences. Generated tokens are passed
                through `streamer.put(token_ids)` and the streamer is responsible for any further processing.
            negative_prompt_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                The negative prompt needed for some processors such as CFG. The batch size must match the input batch
                size. This is an experimental feature, subject to breaking API changes in future versions.
            negative_prompt_attention_mask (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Attention_mask for `negative_prompt_ids`.
            custom_generate (`str` or `Callable`, *optional*):
                One of the following:
                - `str` (Hugging Face Hub repository name): runs the custom `generate` function defined at
                  `custom_generate/generate.py` in that repository instead of the standard `generate` method. The
                  repository fully replaces the generation logic, and the return type may differ.
                - `str` (local repository path): same as above but from a local path, `trust_remote_code` not required.
                - `Callable`: `generate` will perform the usual input preparation steps, then call the provided callable to
                  run the decoding loop.
                For more information, see [the docs](../../generation_strategies#custom-generation-methods).
            kwargs (`dict[str, Any]`, *optional*):
                Ad hoc parametrization of `generation_config` and/or additional model-specific kwargs that will be
                forwarded to the `forward` function of the model. If the model is an encoder-decoder model, encoder
                specific kwargs should not be prefixed and decoder specific kwargs should be prefixed with *decoder_*.

        Return:
            [`~utils.ModelOutput`] or `torch.LongTensor`: A [`~utils.ModelOutput`] (if `return_dict_in_generate=True`
            or when `config.return_dict_in_generate=True`) or a `torch.LongTensor`.

                If the model is *not* an encoder-decoder model (`model.config.is_encoder_decoder=False`), the possible
                [`~utils.ModelOutput`] types are:

                    - [`~generation.GenerateDecoderOnlyOutput`],
                    - [`~generation.GenerateBeamDecoderOnlyOutput`]

                If the model is an encoder-decoder model (`model.config.is_encoder_decoder=True`), the possible
                [`~utils.ModelOutput`] types are:

                    - [`~generation.GenerateEncoderDecoderOutput`],
                    - [`~generation.GenerateBeamEncoderDecoderOutput`]
        """
        # 0.a. If requested, load an arbitrary generation recipe from the Hub and run it instead
        trust_remote_code = kwargs.pop("trust_remote_code", None)

        if custom_generate is not None and isinstance(custom_generate, str):
            # Get all `generate` arguments in a single variable. Custom functions are responsible for handling them:
            # they receive the same inputs as `generate`, with `model` instead of `self` and excluding the arguments to
            # trigger the custom generation. They can access to methods from `GenerationMixin` through `model`.
            global_keys_to_exclude = {
                "self",
                "kwargs",
                "global_keys_to_exclude",
                "trust_remote_code",
                "custom_generate",
            }
            generate_arguments = {key: value for key, value in locals().items() if key not in global_keys_to_exclude}
            generate_arguments.update(kwargs)

            custom_generate_function = self.load_custom_generate(
                custom_generate, trust_remote_code=trust_remote_code, **kwargs
            )
            return custom_generate_function(model=self, **generate_arguments)

        # 0.b. If requested, switched to continuous batching generation
        if kwargs.get("cache_implementation") == "paged":
            logger.warning(
                "Detected cache_implementation=paged: switching to continuous batching. You should consider using "
                "generate_batch directly instead."
            )

            # generate_batch expects a list of lists of ints, so we create it from the inputs or input_ids
            inputs = inputs if inputs is not None else kwargs.get("input_ids")
            if inputs is None:
                raise ValueError("inputs or input_ids must be provided for CB generation.")

            if inputs.dim() == 1:
                inputs = inputs.unsqueeze(0).tolist()
            elif inputs.dim() == 2:
                inputs = inputs.tolist()
            else:
                raise ValueError(f"inputs must be a 1D or 2D tensor, got {inputs.dim() = }")

            # some arguments are not supported for continuous batching
            if stopping_criteria is not None:
                raise NotImplementedError(
                    f"stopping_criteria is not supported for continuous batching. Got {stopping_criteria = }"
                )
            if prefix_allowed_tokens_fn is not None:
                raise NotImplementedError(
                    f"prefix_allowed_tokens_fn is not supported for continuous batching. Got {prefix_allowed_tokens_fn = }"
                )
            if assistant_model is not None:
                raise NotImplementedError(
                    f"assistant_model is not supported for continuous batching. Got {assistant_model = }"
                )
            if streamer is not None:  # TODO: actually this could be supported
                raise NotImplementedError(f"streaming is not supported for continuous batching. Got {streamer = }")
            if negative_prompt_ids is not None:
                raise NotImplementedError(
                    f"negative_prompt_ids is not supported for continuous batching. Got {negative_prompt_ids = }"
                )
            if negative_prompt_attention_mask is not None:
                raise NotImplementedError(
                    f"negative_prompt_attention_mask is not supported for continuous batching. Got {negative_prompt_attention_mask = }"
                )

            # others are ignored
            if synced_gpus is not None:
                logger.warning(f"synced_gpus is not ignored for continuous batching. Got {synced_gpus = }")
            num_return_sequences = kwargs.get("num_return_sequences", 1)
            num_beams = kwargs.get("num_beams", 1)
            if num_return_sequences > 1 or num_beams > 1:  # FIXME: remove this once CB supports it (which is planned)
                logger.warning(
                    f"num_return_sequences and num_beams are not supported for continuous batching yet. "
                    f"Got {num_return_sequences = } and {num_beams = }. "
                )

            # switch to CB
            outputs = self.generate_batch(
                inputs=inputs,
                generation_config=self._prepare_generation_config(generation_config, **kwargs)[0],
                **kwargs,
            )
            sequences = [
                outputs[f"req_{i}"].prompt_ids + outputs[f"req_{i}"].generated_tokens for i in range(len(outputs))
            ]

            # To use the same indexing (outputs[0]) as the regular generate method, we unsqueeze the tensor
            sequences_as_tensor = torch.tensor(sequences, dtype=torch.long, device=self.device)
            sequences_as_tensor = sequences_as_tensor.unsqueeze(0)
            return sequences_as_tensor

        # 1. Handle kwargs, `generation_config`, validate them and obtain generation mode
        generation_mode_kwargs = self._extract_generation_mode_kwargs(
            custom_generate,
            kwargs,
            synced_gpus,
            assistant_model,
            streamer,
        )

        # Check length values before updating the config with defaults. We'll use it later to define the final min/max length (# 6)
        has_default_max_length = (
            kwargs.get("max_length") is None
            and (generation_config is None or generation_config.max_length is None)
            and self.generation_config.max_length is None
        )
        has_default_min_length = (
            kwargs.get("min_length") is None
            and (generation_config is None or generation_config.min_length is None)
            and self.generation_config.min_length is None
        )
        generation_config, model_kwargs = self._prepare_generation_config(generation_config, **kwargs)

        generation_mode = generation_config.get_generation_mode(assistant_model)
        deprecated_mode_repo = self._get_deprecated_gen_repo(generation_mode, trust_remote_code, custom_generate)

        if isinstance(custom_generate, Callable):
            decoding_method = custom_generate
        elif deprecated_mode_repo is None:
            # type() required to access the unbound class-level method
            decoding_method = getattr(type(self), GENERATION_MODES_MAPPING[generation_mode])

        self._validate_model_kwargs(model_kwargs.copy())
        self._validate_generation_mode(generation_mode, generation_config, generation_mode_kwargs)

        # Deprecation-related step: set Hub repo for deprecated strategies.
        # NOTE: This must come after initializing generation_config, since we need it to determine if this is a deprecated mode.
        # It must also be before any preparation steps, since Hub repos expect to be loaded before preparation steps.
        # TODO joao, manuel: remove this in v4.62.0
        if deprecated_mode_repo is not None:
            return GenerationMixin.generate(
                self,
                inputs=inputs,
                generation_config=generation_config,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
                prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
                assistant_model=assistant_model,
                negative_prompt_ids=negative_prompt_ids,
                negative_prompt_attention_mask=negative_prompt_attention_mask,
                custom_generate=deprecated_mode_repo,
                trust_remote_code=trust_remote_code,
                **generation_mode_kwargs,
                **kwargs,
            )

        # 2. Set generation parameters if not already defined
        logits_processor = logits_processor if logits_processor is not None else LogitsProcessorList()
        stopping_criteria = stopping_criteria if stopping_criteria is not None else StoppingCriteriaList()

        accepts_attention_mask = "attention_mask" in set(inspect.signature(self.forward).parameters.keys())
        kwargs_has_attention_mask = model_kwargs.get("attention_mask", None) is not None

        # 3. Define model inputs
        inputs_tensor, model_input_name, model_kwargs = self._prepare_model_inputs(
            inputs, generation_config.bos_token_id, model_kwargs
        )
        # Some generation modes (e.g. assisted) need `inputs_tensor` to rerun encoder.forward()
        if "inputs_tensor" in inspect.signature(decoding_method).parameters.keys():
            generation_mode_kwargs["inputs_tensor"] = inputs_tensor
        batch_size = inputs_tensor.shape[0]

        device = inputs_tensor.device
        self._prepare_special_tokens(generation_config, kwargs_has_attention_mask, device=device)

        # decoder-only models must use left-padding for batched generation.
        if not self.config.is_encoder_decoder:
            # If `input_ids` was given, check if the last id in any sequence is `pad_token_id`
            # Note: If using, `inputs_embeds` this check does not work, because we want to be more hands-off.
            if generation_config._pad_token_tensor is not None and batch_size > 1 and len(inputs_tensor.shape) == 2:
                # When an attention mask is provided, use it to detect right-padding (more reliable than
                # checking token ids, which can produce false positives when pad_token_id == eos_token_id
                # or pad_token_id == bos_token_id, as is the case for Qwen3 and other models).
                attention_mask = model_kwargs.get("attention_mask", None)
                if attention_mask is not None and attention_mask.shape == inputs_tensor.shape:
                    # Right-padding means there are zeros (masked positions) at the end of some sequences
                    has_right_padding = torch.any(attention_mask[:, -1] == 0).item()
                else:
                    # Fallback: check if the last token is a pad token (original heuristic)
                    has_right_padding = torch.sum(inputs_tensor[:, -1] == generation_config._pad_token_tensor) > 0
                if has_right_padding:
                    logger.warning(
                        "A decoder-only architecture is being used, but right-padding was detected! For correct "
                        "generation results, please set `padding_side='left'` when initializing the tokenizer."
                    )

        # 4. Define other model kwargs
        # decoder-only models with inputs_embeds forwarding must use caching (otherwise we can't detect whether we are
        # generating the first new token or not, and we only want to use the embeddings for the first new token)
        if not self.config.is_encoder_decoder and model_input_name == "inputs_embeds":
            generation_config.use_cache = True

        if not kwargs_has_attention_mask and not self.config.is_encoder_decoder and accepts_attention_mask:
            model_kwargs["attention_mask"] = self._prepare_attention_mask_for_generation(
                inputs_tensor, generation_config, model_kwargs
            )
        elif kwargs_has_attention_mask:
            # TODO (joao): generalize this check with other types of inputs
            if model_input_name == "input_ids" and len(model_kwargs["attention_mask"].shape) > 2:
                raise ValueError("`attention_mask` passed to `generate` must be 2D.")

        kwargs_has_position_ids = model_kwargs.get("position_ids", None) is not None
        accepts_position_ids = "position_ids" in set(inspect.signature(self.forward).parameters.keys())
        if not kwargs_has_position_ids and accepts_position_ids and not self.config.is_encoder_decoder:
            model_kwargs["position_ids"] = self._prepare_position_ids_for_generation(inputs_tensor, model_kwargs)

        if self.config.is_encoder_decoder and "encoder_outputs" not in model_kwargs:
            # if model is encoder decoder encoder_outputs are created and added to `model_kwargs`
            model_kwargs = self._prepare_encoder_decoder_kwargs_for_generation(
                inputs_tensor, model_kwargs, model_input_name, generation_config
            )

        # 5. Prepare `input_ids` which will be used for auto-regressive generation
        if self.config.is_encoder_decoder:
            input_ids, model_kwargs = self._prepare_decoder_input_ids_for_generation(
                batch_size=batch_size,
                model_input_name=model_input_name,
                model_kwargs=model_kwargs,
                decoder_start_token_id=generation_config._decoder_start_token_tensor,
                device=inputs_tensor.device,
            )
        else:
            input_ids = inputs_tensor if model_input_name == "input_ids" else model_kwargs.pop("input_ids")

        # Expand inputs depending on the generation mode
        input_ids, model_kwargs = self._expand_inputs_for_generation(
            input_ids=input_ids,
            expand_size=max(generation_config.num_beams, generation_config.num_return_sequences),
            is_encoder_decoder=self.config.is_encoder_decoder,
            **model_kwargs,
        )

        if generation_config.token_healing:
            input_ids = self.heal_tokens(input_ids, generation_mode_kwargs.get("tokenizer"))

        if streamer is not None:
            streamer.put(input_ids.cpu())

        # 6. Prepare `max_length` depending on other stopping criteria.
        input_ids_length = input_ids.shape[1]
        generation_config = self._prepare_generated_length(
            generation_config=generation_config,
            has_default_max_length=has_default_max_length,
            has_default_min_length=has_default_min_length,
            model_input_name=model_input_name,
            inputs_tensor=inputs_tensor,
            input_ids_length=input_ids_length,
        )

        # If the model supports `logits_to_keep` in forward(), set it to 1 to avoid computing the whole
        # logit matrix. This can save a lot of memory during the first forward pass. Note that assisted decoding
        # dynamically overrides this value as it can need more than the last token logits
        if self._supports_logits_to_keep() and "logits_to_keep" not in model_kwargs:
            model_kwargs["logits_to_keep"] = 1

        self._validate_generated_length(generation_config, input_ids_length, has_default_max_length)

        # 7. Prepare the cache.
        # - `model_kwargs` may be updated in place with a cache as defined by the parameters in `generation_config`.
        # - different models have a different cache name expected by the model (default = "past_key_values")
        # - `max_length`, prepared above, is used to determine the maximum cache length
        max_cache_length = generation_config.max_length - 1
        if (
            inputs_tensor.shape[1] != input_ids_length
            and model_input_name == "inputs_embeds"
            and not self.config.is_encoder_decoder
        ):
            max_cache_length += inputs_tensor.shape[1]
        self._prepare_cache_for_generation(
            generation_config, model_kwargs, generation_mode, batch_size, max_cache_length
        )

        if self.device.type != input_ids.device.type:
            warnings.warn(
                "You are calling .generate() with the `input_ids` being on a device type different"
                f" than your model's device. `input_ids` is on {input_ids.device.type}, whereas the model"
                f" is on {self.device.type}. You may experience unexpected behaviors or slower generation."
                " Please make sure that you have put `input_ids` to the"
                f" correct device by calling for example input_ids = input_ids.to('{self.device.type}') before"
                " running `.generate()`.",
                UserWarning,
            )

        # 8. Prepare logits processors and stopping criteria
        prepared_logits_processor = self._get_logits_processor(
            generation_config=generation_config,
            input_ids_seq_length=input_ids_length,
            encoder_input_ids=inputs_tensor,
            prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
            logits_processor=logits_processor,
            device=inputs_tensor.device,
            model_kwargs=model_kwargs,
            negative_prompt_ids=negative_prompt_ids,
            negative_prompt_attention_mask=negative_prompt_attention_mask,
        )
        prepared_stopping_criteria = self._get_stopping_criteria(
            generation_config=generation_config,
            stopping_criteria=stopping_criteria,
            tokenizer=generation_mode_kwargs.get("tokenizer"),
        )

        # Set model_kwargs `use_cache` so we can use it later in forward runs
        model_kwargs["use_cache"] = generation_config.use_cache

        # 9. Call generation mode
        result = decoding_method(
            self,
            input_ids,
            logits_processor=prepared_logits_processor,
            stopping_criteria=prepared_stopping_criteria,
            generation_config=generation_config,
            **generation_mode_kwargs,
            **model_kwargs,
        )

        return result