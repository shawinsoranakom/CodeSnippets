def _check_gradient_accumulation(
        self,
        base_batch_size,
        gas_batch_size,
        gas_steps,
        loss_tolerance,
        model_accepts_loss_kwargs=True,
        compute_loss_func=None,
    ):
        """
        Train twice with the same effective batch (base_batch_size vs gas_batch_size * gas_steps)
        and assert grad norms and losses match.
        """
        model_name = self._ga_model_name
        args_kwargs = {"logging_steps": 1, "max_steps": 3, "learning_rate": 1e-4, "max_grad_norm": 0.0}
        trainer_kwargs = {"train_dataset": self._ga_dataset, "data_collator": self._ga_data_collator}
        if compute_loss_func is not None:
            trainer_kwargs["compute_loss_func"] = compute_loss_func

        with tempfile.TemporaryDirectory() as tmp_dir:
            model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32)
            args = TrainingArguments(
                tmp_dir, per_device_train_batch_size=base_batch_size, gradient_accumulation_steps=1, **args_kwargs
            )
            base_callback = StoreLossCallback()
            trainer = Trainer(model, args, callbacks=[base_callback], **trainer_kwargs)
            if not model_accepts_loss_kwargs:
                trainer.model_accepts_loss_kwargs = False
            trainer.train()
            base_grad_norms = [h["grad_norm"] for h in trainer.state.log_history if "grad_norm" in h]

            model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.float32)
            args = TrainingArguments(
                tmp_dir,
                per_device_train_batch_size=gas_batch_size,
                gradient_accumulation_steps=gas_steps,
                **args_kwargs,
            )
            gas_callback = StoreLossCallback()
            trainer = Trainer(model, args, callbacks=[gas_callback], **trainer_kwargs)
            if not model_accepts_loss_kwargs:
                trainer.model_accepts_loss_kwargs = False
            trainer.train()
            gas_grad_norms = [h["grad_norm"] for h in trainer.state.log_history if "grad_norm" in h]

        for step, (base_gn, gas_gn) in enumerate(zip(base_grad_norms, gas_grad_norms)):
            ratio = gas_gn / base_gn if base_gn > 0 else float("inf")
            self.assertAlmostEqual(
                ratio, 1.0, delta=0.1, msg=f"Step {step}: grad_norm ratio {ratio:.2f} — GAS leak suspected"
            )
        loss_diff = [abs(b - g) for b, g in zip(base_callback.losses, gas_callback.losses)]
        self.assertLess(max(loss_diff), loss_tolerance, f"Loss difference {max(loss_diff)} exceeds {loss_tolerance}")