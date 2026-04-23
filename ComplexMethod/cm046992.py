def patch_gradient_accumulation_fix(Trainer):
    # Fixes gradient accumulation
    # Fixes Output 0 of UnslothFusedLossBackward is a view and is being modified inplace.
    import inspect

    if hasattr(Trainer, "get_batch_samples"):
        if Trainer.get_batch_samples.__name__ == "_unsloth_get_batch_samples":
            return
        if (
            not inspect.getsource(Trainer.get_batch_samples)
            .strip()
            .endswith("return batch_samples, num_items_in_batch")
        ):
            raise NotImplementedError(
                "Unsloth: Please make a Github issue immediately!!"
            )
        else:
            if Trainer.get_batch_samples.__name__ != "_unsloth_get_batch_samples":
                Trainer.get_batch_samples = _unsloth_get_batch_samples

            # Also fix passing in num_items_in_batch
            if not hasattr(Trainer, "_old_compute_loss"):
                # Fix transformers 4.57.0 causing `Output 0 of UnslothFusedLossBackward is a view and is being modified inplace.`
                function = inspect.getsource(Trainer.compute_loss)
                if "loss *=" in function or "loss*=" in function:
                    where = function.find("def")
                    function = function.split("\n")
                    function = "\n".join(x[where:] for x in function)

                    # Import all variables that need importing
                    import transformers.trainer

                    items_in_trainer = dir(transformers.trainer)
                    good_items = []
                    for item in items_in_trainer:
                        if item in function:
                            good_items.append(item)
                    exec(
                        "from transformers.trainer import ("
                        + ", ".join(x for x in good_items)
                        + ")",
                        globals(),
                    )

                    # Replace loss*= with loss = loss *
                    function = re.sub(
                        r"loss[\s]{0,}\*\=",
                        "loss = loss *",
                        function,
                    )
                    exec(function, globals())
                    Trainer.compute_loss = compute_loss
                Trainer._old_compute_loss = Trainer.compute_loss
                Trainer.compute_loss = _unsloth_pre_compute_loss
    else:
        logger.warning_once(
            "Unsloth: We fixed a gradient accumulation bug, "
            "but it seems like you don't have the latest transformers version!\n"
            "Please update transformers, TRL and unsloth via:\n"
            "`pip install --upgrade --no-cache-dir --no-deps unsloth transformers git+https://github.com/huggingface/trl.git`"
        )

    # Also fix up loss scaling ie negate loss *= self.args.gradient_accumulation_steps
    if not (
        Trainer.training_step.__name__ == "_unsloth_training_step"
        or "num_items_in_batch"
        not in inspect.signature(Trainer.training_step).parameters
    ):
        function = inspect.getsource(Trainer.training_step)
        where = function.find("def")
        function = function.split("\n")
        function = "\n".join(x[where:] for x in function)

        # Import all variables that need importing
        import transformers.trainer

        items_in_trainer = dir(transformers.trainer)
        good_items = []
        for item in items_in_trainer:
            if item in function:
                good_items.append(item)
        exec(
            "from transformers.trainer import ("
            + ", ".join(x for x in good_items)
            + ")",
            globals(),
        )

        # Accelerate does / self.args.gradient_accumulation_steps internally, so if we already
        # summed it up and did the division before hand, we have to negate it.
        function = function.replace(
            "loss *= self.args.gradient_accumulation_steps",
            "if num_items_in_batch is not None: loss *= self.args.gradient_accumulation_steps",
        )
        function = function.replace(
            "def training_step", "def _unsloth_training_step", 1
        )

        # Fix 4.47.0 issue where num_items_in_batch was removed
        # See https://github.com/huggingface/transformers/pull/35121
        function = function.replace(
            "if self.model_accepts_loss_kwargs:",
            "if False:",
        )

        # Fix when num_items_in_batch is nothing
        # https://github.com/huggingface/transformers/pull/35207
        function = re.sub(
            r"else:\n"
            r"([\s]{4,})self\.accelerator\.backward\(loss, \*\*kwargs\)\n"
            r"(.+?)if num_items_in_batch is None\:\n"
            r"(.+?)return loss\.detach\(\) \/ self\.args\.gradient_accumulation_steps",
            "else:\n"
            "\2if num_items_in_batch is None:\n"
            "\3loss = loss / self.args.gradient_accumulation_steps\n"
            "\1self.accelerator.backward(loss, **kwargs)",
            function,
        )

        exec(function, globals())
        Trainer.training_step = _unsloth_training_step

    # Wrap Trainer.__init__: (1) pre-init, shadow accepts_loss_kwargs on whatever
    # model was passed in (covers PEFT wrapping done after FastModel.from_pretrained);
    # (2) post-init, clamp accelerator GA to 1 for the transformers 5.0-5.5
    # GradientAccumulationPlugin regression. No-op on 4.x and 5.6+. See #4982.
    if not getattr(Trainer, "_unsloth_init_wrapped_for_accelerate_gas", False):
        _original_trainer_init = Trainer.__init__

        def _unsloth_trainer_init(self, *args, **kwargs):
            model = kwargs.get("model")
            if model is None and len(args) > 0:
                model = args[0]
            if model is not None:
                try:
                    apply_accepts_loss_kwargs_fix(model)
                except Exception:
                    pass
            _original_trainer_init(self, *args, **kwargs)
            try:
                accelerator = getattr(self, "accelerator", None)
                if (
                    accelerator is not None
                    and getattr(accelerator, "gradient_accumulation_steps", 1) > 1
                ):
                    accelerator.gradient_accumulation_steps = 1
                    gs = getattr(accelerator, "gradient_state", None)
                    if gs is not None and hasattr(gs, "plugin_kwargs"):
                        try:
                            gs.plugin_kwargs["num_steps"] = 1
                        except Exception:
                            pass
            except Exception:
                pass

        _unsloth_trainer_init.__wrapped__ = _original_trainer_init
        Trainer.__init__ = _unsloth_trainer_init
        Trainer._unsloth_init_wrapped_for_accelerate_gas = True