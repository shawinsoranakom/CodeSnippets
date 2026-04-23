def _validate_args(self) -> None:
        """Validate constructor arguments and fail fast on incompatible combinations."""
        args = self.args

        # --- SageMaker Model Parallel mixed-precision validation ---
        if is_sagemaker_mp_enabled():
            if args.bf16:
                raise ValueError("SageMaker Model Parallelism does not support BF16 yet. Please use FP16 instead ")
            if args.fp16 != smp.state.cfg.fp16:
                logger.warning(
                    f"FP16 provided in SM_HP_MP_PARAMETERS is {smp.state.cfg.fp16}, "
                    f"but FP16 provided in trainer argument is {args.fp16}, "
                    f"setting to {smp.state.cfg.fp16}"
                )
                args.fp16 = smp.state.cfg.fp16

        # --- Training-argument validations ---
        if args.batch_eval_metrics and self.compute_metrics is not None:
            if "compute_result" not in inspect.signature(self.compute_metrics).parameters:
                raise ValueError(
                    "When using `batch_eval_metrics`, your `compute_metrics` function must take a `compute_result`"
                    " boolean argument which will be triggered after the last batch of the eval set to signal that the"
                    " summary statistics should be returned by the function."
                )
        if args.eval_strategy is not None and args.eval_strategy != "no" and self.eval_dataset is None:
            raise ValueError(
                f"You have set `args.eval_strategy` to {args.eval_strategy} but you didn't pass an `eval_dataset` to `Trainer`. Either set `args.eval_strategy` to `no` or pass an `eval_dataset`. "
            )
        if args.save_strategy == SaveStrategy.BEST or args.load_best_model_at_end:
            if args.metric_for_best_model is None:
                raise ValueError(
                    "`args.metric_for_best_model` must be provided when using 'best' save_strategy or if `args.load_best_model_at_end` is set to `True`."
                )

        # --- Optimizer validations ---
        if self.optimizer_cls_and_kwargs is not None and self.optimizer is not None:
            raise RuntimeError("Passing both `optimizers` and `optimizer_cls_and_kwargs` arguments is incompatible.")
        if self.model_init is not None and (self.optimizer is not None or self.lr_scheduler is not None):
            raise RuntimeError(
                "Passing a `model_init` is incompatible with providing the `optimizers` argument. "
                "You should subclass `Trainer` and override the `create_optimizer_and_scheduler` method."
            )
        if is_torch_xla_available() and self.optimizer is not None:
            for param in self.model.parameters():
                model_device = param.device
                break
            for param_group in self.optimizer.param_groups:
                if len(param_group["params"]) > 0:
                    optimizer_device = param_group["params"][0].device
                    break
            if model_device != optimizer_device:
                raise ValueError(
                    "The model and the optimizer parameters are not on the same device, which probably means you"
                    " created an optimizer around your model **before** putting on the device and passing it to the"
                    " `Trainer`. Make sure the lines `import torch_xla.core.xla_model as xm` and"
                    " `model.to(xm.xla_device())` is performed before the optimizer creation in your script."
                )
        if (self.is_fsdp_xla_enabled or self.is_fsdp_enabled) and (
            self.optimizer is not None or self.lr_scheduler is not None
        ):
            raise RuntimeError(
                "Passing `optimizers` is not allowed if PyTorch FSDP is enabled. "
                "You should subclass `Trainer` and override the `create_optimizer_and_scheduler` method."
            )

        # --- Dataset validations ---
        if not callable(self.data_collator) and callable(getattr(self.data_collator, "collate_batch", None)):
            raise TypeError("The `data_collator` should be a simple callable (function, class with `__call__`).")
        if args.max_steps > 0 and args.num_train_epochs > 0:
            logger.info("max_steps is given, it will override any value given in num_train_epochs")
        if self.train_dataset is not None and not has_length(self.train_dataset) and args.max_steps <= 0:
            raise ValueError(
                "The train_dataset does not implement __len__, max_steps has to be specified. "
                "The number of steps needs to be known in advance for the learning rate scheduler."
            )

        if self.train_dataset is not None and isinstance(self.train_dataset, torch.utils.data.IterableDataset):
            logger.info(
                f"The `train_sampling_strategy='{args.train_sampling_strategy}'` option is ignored when using an `IterableDataset`. "
                "Samplers cannot be used with IterableDataset as they require indexed access to the dataset."
            )