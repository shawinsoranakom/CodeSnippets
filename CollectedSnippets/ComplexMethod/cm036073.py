def _init(
        self,
        model_name: str,
        dtype: str = "auto",
        *,
        revision: str | None = None,
        model_kwargs: dict[str, Any] | None = None,
        trust_remote_code: bool = True,
        is_sentence_transformer: bool = False,
        is_cross_encoder: bool = False,
        skip_tokenizer_init: bool = False,
        auto_cls: type[_BaseAutoModelClass] = AutoModelForCausalLM,
    ) -> None:
        model_name = maybe_model_redirect(model_name)
        self.model_name = model_name

        self.config = AutoConfig.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
        )
        # HF runner should use the HF config so that it's consistent with the HF model
        if self.config.__module__.startswith("vllm.transformers_utils.configs"):
            from transformers.models.auto.configuration_auto import CONFIG_MAPPING

            del CONFIG_MAPPING._extra_content[self.config.model_type]
            self.config = AutoConfig.from_pretrained(
                model_name,
                trust_remote_code=trust_remote_code,
            )
        self.device = self.get_default_device()
        self.dtype = dtype = _get_and_verify_dtype(
            self.model_name,
            self.config,
            dtype=dtype,
            is_pooling_model=is_sentence_transformer or is_cross_encoder,
            config_format="hf",
        )

        model_kwargs = model_kwargs if model_kwargs is not None else {}
        model_kwargs.setdefault("dtype", dtype)

        if is_sentence_transformer:
            # Lazy init required for AMD CI
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(
                model_name,
                revision=revision,
                device=self.device,
                model_kwargs=model_kwargs,
                trust_remote_code=trust_remote_code,
            )
        elif is_cross_encoder:
            # Lazy init required for AMD CI
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(
                model_name,
                revision=revision,
                device=self.device,
                automodel_args=model_kwargs,
                trust_remote_code=trust_remote_code,
            )
        else:
            model = cast(
                nn.Module,
                auto_cls.from_pretrained(
                    model_name,
                    revision=revision,
                    trust_remote_code=trust_remote_code,
                    **model_kwargs,
                ),
            )

            # in case some unquantized custom models are not in same dtype
            if getattr(model, "quantization_method", None) is None and any(
                p.dtype != self.dtype for p in model.parameters()
            ):
                model = model.to(dtype=self.dtype)

            if (
                getattr(model, "quantization_method", None) != "bitsandbytes"
                and len({p.device for p in model.parameters()}) < 2
            ):
                model = model.to(device=self.device)

            self.model = model

        if not skip_tokenizer_init:
            self.tokenizer: "PreTrainedTokenizer | PreTrainedTokenizerFast" = (
                AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=trust_remote_code,
                )
            )

        # don't put this import at the top level
        # it will call torch.accelerator.device_count()
        from transformers import AutoProcessor

        self.processor = AutoProcessor.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
        )
        if skip_tokenizer_init:
            self.tokenizer = self.processor.tokenizer