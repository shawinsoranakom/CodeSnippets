def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer | None = None,
        feature_extractor: PreTrainedFeatureExtractor | None = None,
        image_processor: BaseImageProcessor | None = None,
        processor: ProcessorMixin | None = None,
        task: str = "",
        device: int | torch.device | None = None,
        binary_output: bool = False,
        **kwargs,
    ):
        # We need to pop them for _sanitize_parameters call later
        _, _, _ = kwargs.pop("args_parser", None), kwargs.pop("torch_dtype", None), kwargs.pop("dtype", None)

        self.task = task
        self.model = model
        self.tokenizer = tokenizer
        self.feature_extractor = feature_extractor
        self.image_processor = image_processor
        self.processor = processor

        # `accelerate` device map
        hf_device_map = getattr(self.model, "hf_device_map", None)

        if hf_device_map is not None and device is not None:
            raise ValueError(
                "The model has been loaded with `accelerate` and therefore cannot be moved to a specific device. Please "
                "discard the `device` argument when creating your pipeline object."
            )

        if device is None:
            if hf_device_map is not None:
                # Take the first device used by `accelerate`.
                device = next(iter(hf_device_map.values()))
            else:
                device = 0

        if device == -1 and self.model.device is not None:
            device = self.model.device
        if isinstance(device, torch.device):
            if (device.type == "xpu" and not is_torch_xpu_available(check_device=True)) or (
                device.type == "hpu" and not is_torch_hpu_available()
            ):
                raise ValueError(f'{device} is not available, you should use device="cpu" instead')

            self.device = device
        elif isinstance(device, str):
            if ("xpu" in device and not is_torch_xpu_available(check_device=True)) or (
                "hpu" in device and not is_torch_hpu_available()
            ):
                raise ValueError(f'{device} is not available, you should use device="cpu" instead')

            self.device = torch.device(device)
        elif device < 0:
            self.device = torch.device("cpu")
        elif is_torch_mlu_available():
            self.device = torch.device(f"mlu:{device}")
        elif is_torch_musa_available():
            self.device = torch.device(f"musa:{device}")
        elif is_torch_cuda_available():
            self.device = torch.device(f"cuda:{device}")
        elif is_torch_npu_available():
            self.device = torch.device(f"npu:{device}")
        elif is_torch_hpu_available():
            self.device = torch.device(f"hpu:{device}")
        elif is_torch_xpu_available(check_device=True):
            self.device = torch.device(f"xpu:{device}")
        elif is_torch_mps_available():
            self.device = torch.device(f"mps:{device}")
        else:
            self.device = torch.device("cpu")

        if torch.distributed.is_available() and torch.distributed.is_initialized():
            self.device = self.model.device
        logger.debug(f"Device set to use {self.device}")

        self.binary_output = binary_output

        # We shouldn't call `model.to()` for models loaded with accelerate as well as the case that model is already on device
        if (
            self.model.device != self.device
            and not (isinstance(self.device, int) and self.device < 0)
            and hf_device_map is None
        ):
            self.model.to(self.device)

        # If it's a generation pipeline and the model can generate:
        # 1 - create a local generation config. This is done to avoid side-effects on the model as we apply local
        # tweaks to the generation config.
        # 2 - load the assistant model if it is passed.
        if self._pipeline_calls_generate and self.model.can_generate():
            self.assistant_model, self.assistant_tokenizer = load_assistant_model(
                self.model, kwargs.pop("assistant_model", None), kwargs.pop("assistant_tokenizer", None)
            )
            self.prefix = self.model.config.prefix if hasattr(self.model.config, "prefix") else None
            # each pipeline with text generation capabilities should define its own default generation in a
            # `_default_generation_config` class attribute
            default_pipeline_generation_config = getattr(self, "_default_generation_config", GenerationConfig())
            if hasattr(self.model, "_prepare_generation_config"):
                # Uses `generate`'s logic to enforce the following priority of arguments:
                # 1. user-defined config options in `**kwargs`
                # 2. model's generation config values
                # 3. pipeline's default generation config values
                # NOTE: _prepare_generation_config creates a deep copy of the generation config before updating it,
                # and returns all kwargs that were not used to update the generation config
                prepared_generation_config, kwargs = self.model._prepare_generation_config(
                    generation_config=default_pipeline_generation_config, **kwargs
                )
                self.generation_config = prepared_generation_config
                # if the `max_new_tokens` is set to the pipeline default, but `max_length` is set to a non-default
                # value: let's honor `max_length`. E.g. we want Whisper's default `max_length=448` take precedence
                # over over the pipeline's length default.
                if (
                    default_pipeline_generation_config.max_new_tokens is not None  # there's a pipeline default
                    and self.generation_config.max_new_tokens == default_pipeline_generation_config.max_new_tokens
                    and self.generation_config.max_length is not None
                    and self.generation_config.max_length != 20  # global default
                ):
                    self.generation_config.max_new_tokens = None
            else:
                # TODO (joao): no PT model should reach this line. However, some audio models with complex
                # inheritance patterns do. Streamline those models such that this line is no longer needed.
                # In those models, the default generation config is not (yet) used.
                self.generation_config = copy.deepcopy(self.model.generation_config)
            # Update the generation config with task specific params if they exist.
            # NOTE: 1. `prefix` is pipeline-specific and doesn't exist in the generation config.
            #       2. `task_specific_params` is a legacy feature and should be removed in a future version.
            task_specific_params = getattr(self.model.config, "task_specific_params", None)
            if task_specific_params is not None and task in task_specific_params:
                this_task_params = task_specific_params.get(task)
                if "prefix" in this_task_params:
                    self.prefix = this_task_params.pop("prefix")
                self.generation_config.update(**this_task_params)
            # If the tokenizer has a pad token but the model doesn't, set it so that `generate` is aware of it.
            if (
                self.tokenizer is not None
                and self.tokenizer.pad_token_id is not None
                and self.generation_config.pad_token_id is None
            ):
                self.generation_config.pad_token_id = self.tokenizer.pad_token_id

        self.call_count = 0
        self._batch_size = kwargs.pop("batch_size", None)
        self._num_workers = kwargs.pop("num_workers", None)
        self._preprocess_params, self._forward_params, self._postprocess_params = self._sanitize_parameters(**kwargs)

        # In processor only mode, we can get the modality processors from the processor
        if self.processor is not None and all(
            [self.tokenizer is None, self.feature_extractor is None, self.image_processor is None]
        ):
            self.tokenizer = getattr(self.processor, "tokenizer", None)
            self.feature_extractor = getattr(self.processor, "feature_extractor", None)
            self.image_processor = getattr(self.processor, "image_processor", None)

        if self.image_processor is None and self.feature_extractor is not None:
            if isinstance(self.feature_extractor, BaseImageProcessor):
                # Backward compatible change, if users called
                # ImageSegmentationPipeline(.., feature_extractor=MyFeatureExtractor())
                # then we should keep working
                self.image_processor = self.feature_extractor