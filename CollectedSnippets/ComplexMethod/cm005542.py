def __init__(
        self,
        input_ids: torch.LongTensor,
        assistant_model: "PreTrainedModel",
        generation_config: "GenerationConfig",
        model_kwargs: dict,
        inputs_tensor: torch.Tensor | None = None,
        logits_processor: Optional["LogitsProcessorList"] = None,
    ):
        # Make sure all data at the same device as assistant model
        device = assistant_model.device
        input_ids = input_ids.to(device)
        if inputs_tensor is not None:
            inputs_tensor = inputs_tensor.to(device)

        # Prepare the assistant and the starting number of candidate tokens
        self.assistant_model = assistant_model

        # Prepare the generation config by updating with default values if not already set by users
        self.assistant_generation_config = copy.deepcopy(assistant_model.generation_config)
        global_defaults = self.assistant_generation_config._get_default_generation_params()
        self.assistant_generation_config.update(**global_defaults, defaults_only=True)
        self.num_assistant_tokens = self.assistant_generation_config.num_assistant_tokens
        self.assistant_confidence_threshold = self.assistant_generation_config.assistant_confidence_threshold

        # Set eos in assistant same as in target model
        self.assistant_generation_config.eos_token_id = generation_config.eos_token_id

        # Prepare the kwargs for the assistant model
        assistant_kwargs = {}
        for key, value in model_kwargs.items():  # deepcopy crashes if we attempt to copy encoder outputs with grads
            if key not in ("encoder_outputs", "past_key_values"):
                assistant_kwargs[key] = (
                    value.detach().to(device) if isinstance(value, torch.Tensor) else copy.deepcopy(value)
                )

        # Remove potential default "logits_to_keep" key
        if "logits_to_keep" in assistant_kwargs and not assistant_model._supports_logits_to_keep():
            del assistant_kwargs["logits_to_keep"]

        # If the assistant is an encoder-decoder model, assume the encoder is different on the assistant.
        if assistant_model.config.is_encoder_decoder:
            inputs_tensor, model_input_name, assistant_kwargs = assistant_model._prepare_model_inputs(
                inputs_tensor, self.assistant_generation_config.bos_token_id, assistant_kwargs
            )
            assistant_kwargs = assistant_model._prepare_encoder_decoder_kwargs_for_generation(
                inputs_tensor, assistant_kwargs, model_input_name, self.assistant_generation_config
            )
        elif "encoder_outputs" in model_kwargs:
            assistant_kwargs["encoder_outputs"] = model_kwargs["encoder_outputs"]
        self.assistant_kwargs = assistant_kwargs

        # Prepare assistant model's keys of inputs
        if assistant_model.config.is_encoder_decoder:
            # both are encoder-decoder
            self.input_ids_key = "decoder_input_ids"
        elif "encoder_outputs" in assistant_kwargs:
            # special case for encoder-decoder with decoder-only assistant (like DistilWhisper)
            self.input_ids_key = "input_ids"
            self.assistant_kwargs["attention_mask"] = self.assistant_kwargs.get(
                "decoder_attention_mask",
                torch.ones((input_ids.shape[0], 1), device=input_ids.device, dtype=torch.long),
            )
        else:
            # both are decoder-only
            self.input_ids_key = "input_ids"

        # Prepare generation-related options.
        self.logits_processor = logits_processor if logits_processor is not None else LogitsProcessorList()
        self.generation_config = copy.deepcopy(generation_config)

        self.generation_config.return_dict_in_generate = True
        self.generation_config.output_scores = True
        self.generation_config.assistant_confidence_threshold = self.assistant_confidence_threshold
        # this flag allow us set the confidence stopping criteria for assistant model generation.
        self.generation_config.is_assistant = True

        # avoid unnecessary warnings that min_length is larger than max_new_tokens
        # remove the `MinLengthLogitsProcessor` if exists (NOTE: no need to check for `MinNewTokensLogitsProcessor`)
        self.main_model_min_length = self.generation_config.min_length
        self.generation_config.min_length = None
        self.generation_config.min_new_tokens = None
        self.main_model_max_length = self.generation_config.max_length
        self.generation_config.max_length = None
        self.logits_processor = [
            processor for processor in self.logits_processor if not isinstance(processor, MinLengthLogitsProcessor)
        ]

        # We need to roll back the cache in assisted generation, only DynamicCache is supported
        self.generation_config.cache_implementation = "dynamic_full"

        if (
            is_sklearn_available()
            and self.assistant_generation_config.assistant_confidence_threshold
            and type(self) is AssistedCandidateGenerator
        ):
            self.probs = []
            self.matches = []