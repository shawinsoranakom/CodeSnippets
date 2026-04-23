def setup_benchmark(self, model_id: str, config: BenchmarkConfig) -> None:
        # Some attributes only need to be set once per model
        if self._setup_for != model_id:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            # We set the EOS token to the padding token for open-ended generation
            self.tokenizer.eos_token = self.tokenizer.pad_token
            self._setup_for = model_id

        # Prepare inputs
        self.inputs = self.tokenizer(
            [DEFAULT_PROMPT for _ in range(config.batch_size)],
            return_tensors="pt",
            max_length=config.sequence_length,
            truncation=True,
            return_attention_mask=True,
        )
        self.inputs["use_cache"] = True

        # Prepare generation config
        generation_config_kwargs = {
            "do_sample": False,
            "max_new_tokens": config.num_tokens_to_generate,
        }

        # Add compile config if found
        if config.compile_config is not None:
            generation_config_kwargs.update(compile_config=config.compile_config)
            # To trigger compile in generate, we need to set the cache to static
            if not config.continuous_batching:
                generation_config_kwargs.update(cache_implementation="static")

        generation_config = GenerationConfig(**generation_config_kwargs)

        # Load model
        self.logger.debug(f"Loading model {model_id} on device {config.device}...")
        dtype = getattr(torch, config.dtype.removeprefix("torch."))
        use_kernels = config.kernelize and kernelize is not None and Mode is not None
        device_map = config.device if config.tp_plan is None else None
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            dtype=dtype,
            attn_implementation=config.attn_implementation,
            generation_config=generation_config,
            use_kernels=use_kernels,
            device_map=device_map,
            tp_plan=config.tp_plan,
        )
        self.model = self.model.eval()
        self.inputs = self.inputs.to(self.model.device)