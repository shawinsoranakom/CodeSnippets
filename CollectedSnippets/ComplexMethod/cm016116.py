def load_model(
        self,
        device,
        model_name,
        batch_size=None,
        extra_args=None,
    ):
        if self.args.enable_activation_checkpointing:
            raise NotImplementedError(
                "Activation checkpointing not implemented for Timm models"
            )

        is_training = self.args.training
        use_eval_mode = self.args.use_eval_mode

        channels_last = self._args.channels_last
        model = self._download_model(model_name)

        if model is None:
            raise RuntimeError(f"Failed to load model '{model_name}'")
        model.to(
            device=device,
            memory_format=torch.channels_last if channels_last else None,
        )

        data_config = resolve_data_config(
            vars(self._args) if timmversion >= "0.8.0" else self._args,
            model=model,
            use_test_size=not is_training,
        )
        input_size = data_config["input_size"]
        recorded_batch_size = TIMM_MODELS[model_name]

        batch_size_divisors = self._batch_size["divisors"]
        if model_name in batch_size_divisors:
            recorded_batch_size = max(
                int(recorded_batch_size / batch_size_divisors[model_name]), 1
            )
        batch_size = batch_size or recorded_batch_size

        torch.manual_seed(1337)
        input_tensor = torch.randint(
            256, size=(batch_size,) + input_size, device=device
        ).to(dtype=torch.float32)
        mean = torch.mean(input_tensor)
        std_dev = torch.std(input_tensor)
        example_inputs = (input_tensor - mean) / std_dev

        if channels_last:
            example_inputs = example_inputs.contiguous(
                memory_format=torch.channels_last
            )
        example_inputs = [
            example_inputs,
        ]

        self.loss = torch.nn.CrossEntropyLoss().to(device)

        if model_name in self._config["scaled_compute_loss"]:
            self.compute_loss = self.scaled_compute_loss

        if is_training and not use_eval_mode:
            model.train()
        else:
            model.eval()

        self.validate_model(model_name, model, example_inputs)

        return device, model_name, model, example_inputs, batch_size