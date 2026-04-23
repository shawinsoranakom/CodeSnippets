def create_optimizer(self, model=None) -> torch.optim.Optimizer:
        """
        Setup the optimizer.

        We provide a reasonable default that works well. If you want to use something else, you can pass a tuple in the
        Trainer's init through `optimizers`, or subclass and override this method in a subclass.

        Returns:
            `torch.optim.Optimizer`: The optimizer instance.
        """
        opt_model = self.model if model is None else model

        if self.optimizer is None:
            decay_parameters = self.get_decay_parameter_names(opt_model)
            optimizer_grouped_parameters = [
                {
                    "params": [
                        p for n, p in opt_model.named_parameters() if (n in decay_parameters and p.requires_grad)
                    ],
                    "weight_decay": self.args.weight_decay,
                },
                {
                    "params": [
                        p for n, p in opt_model.named_parameters() if (n not in decay_parameters and p.requires_grad)
                    ],
                    "weight_decay": 0.0,
                },
            ]

            if self.optimizer_cls_and_kwargs is not None:
                optimizer_cls, optimizer_kwargs = self.optimizer_cls_and_kwargs
            else:
                optimizer_cls, optimizer_kwargs = self.get_optimizer_cls_and_kwargs(self.args, opt_model)

            # Check if this is a factory (for complex optimizers like Muon, Dion)
            # Factories are instantiated first, then called with (opt_model, **kwargs)
            if is_optimizer_factory(optimizer_cls):
                self.optimizer = optimizer_cls()(opt_model, **optimizer_kwargs)
            else:
                # Standard optimizer class instantiation
                # Overwrite `params` in case it's created by `get_optimizer_cls_and_kwargs`
                # e.g. for GaLore optimizer.
                if "params" in optimizer_kwargs:
                    optimizer_grouped_parameters = optimizer_kwargs.pop("params")

                # Overwrite `model` in case it's created by `get_optimizer_cls_and_kwargs`
                # e.g. for LOMO optimizer.
                if "model" in optimizer_kwargs:
                    optimizer_grouped_parameters = optimizer_kwargs.pop("model")

                # For layer-wise dummy optimizers we overwrite optimizer_grouped_parameters with `optimizer_dict`
                # to avoid arguments conflicts.
                if "optimizer_dict" in optimizer_kwargs:
                    optimizer_grouped_parameters = optimizer_kwargs.pop("optimizer_dict")

                self.optimizer = optimizer_cls(optimizer_grouped_parameters, **optimizer_kwargs)

            if "bitsandbytes" in str(optimizer_cls) and optimizer_kwargs.get("optim_bits", None) == 8:
                import bitsandbytes

                manager = bitsandbytes.optim.GlobalOptimManager.get_instance()

                skipped = 0
                for module in opt_model.modules():
                    if isinstance(module, nn.Embedding):
                        skipped += sum({p.data_ptr(): p.numel() for p in module.parameters()}.values())
                        logger.info(f"skipped {module}: {skipped / 2**20}M params")
                        manager.register_module_override(module, "weight", {"optim_bits": 32})
                        logger.debug(f"bitsandbytes: will optimize {module} in fp32")
                logger.info(f"skipped: {skipped / 2**20}M params")

        if is_sagemaker_mp_enabled():
            self.optimizer = smp.DistributedOptimizer(self.optimizer)

        return self.optimizer