def load_model(
        self,
        device,
        model_name,
        batch_size=None,
        extra_args=None,
    ):
        is_training = self.args.training
        use_eval_mode = self.args.use_eval_mode
        dtype = torch.float32
        reset_rng_state()

        # Get batch size
        if model_name in BATCH_SIZE_KNOWN_MODELS:
            batch_size_default = BATCH_SIZE_KNOWN_MODELS[model_name]
        elif batch_size is None:
            batch_size_default = 16
            log.info(
                f"Batch size not specified for {model_name}. Setting batch_size=16"  # noqa: G004
            )

        if batch_size is None:
            batch_size = batch_size_default
            batch_size_divisors = self._config["batch_size"]["divisors"]
            if model_name in batch_size_divisors:
                batch_size = max(int(batch_size / batch_size_divisors[model_name]), 1)
                log.info(
                    f"Running smaller batch size={batch_size} for {model_name}, orig batch_size={batch_size_default}"  # noqa: G004
                )

        # Get model and example inputs
        if model_name in HF_LLM_MODELS:
            benchmark_cls = HF_LLM_MODELS[model_name]
            model, example_inputs = benchmark_cls.get_model_and_inputs(
                model_name, device
            )

            # Set this flag so that when we test for speedup, we use
            # model.generate instead of using model.forward
            self.hf_llm = True

            def generate(self, _, example_inputs, collect_outputs=True):
                return model.generate(**example_inputs)

            self.generate = types.MethodType(generate, self)

        else:
            self.hf_llm = False

            model_cls, config = self._get_model_cls_and_config(model_name)
            model = self._download_model(model_name)
            model = model.to(device, dtype=dtype)

            example_inputs = generate_inputs_for_model(
                model_cls, model, model_name, batch_size, device, include_loss_args=True
            )

            # So we can check for correct gradients without eliminating the dropout computation
            for attr in dir(config):
                if "drop" in attr and isinstance(getattr(config, attr), float):
                    setattr(config, attr, 1e-30)

            # Turning off kv cache for torchbench models. This is not the right
            # thing to do, but the pt2 dashboard is outdated. Real transformers
            # benchmarks will be added soon using a different infra.
            if hasattr(model, "config") and hasattr(model.config, "use_cache"):
                model.config.use_cache = False

        if self.args.enable_activation_checkpointing:
            model.gradient_checkpointing_enable()

        if (
            is_training
            and not use_eval_mode
            and not (
                self.args.accuracy and model_name in self._config["only_inference"]
            )
        ):
            model.train()
        else:
            model.eval()

        self.validate_model(model_name, model, example_inputs)
        return device, model_name, model, example_inputs, batch_size