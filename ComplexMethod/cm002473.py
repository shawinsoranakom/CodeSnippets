def _build_accelerator_args(self, **kwargs) -> dict[str, Any]:
        """Helper method to build accelerator-specific keyword arguments."""
        args = {
            "mixed_precision": self.args.mixed_precision,
            "deepspeed_plugin": self.args.deepspeed_plugin,
        }
        args.update(kwargs)

        if self.args.ddp_find_unused_parameters is not None:
            find_unused = self.args.ddp_find_unused_parameters
        elif isinstance(self.model, PreTrainedModel):
            # find_unused_parameters breaks checkpointing as per
            # https://github.com/huggingface/transformers/pull/4659#issuecomment-643356021
            find_unused = not (self.model.is_gradient_checkpointing or self.args.gradient_checkpointing)
        else:
            find_unused = True

        ddp_kwargs = {"find_unused_parameters": find_unused}
        if self.args.ddp_bucket_cap_mb is not None:
            ddp_kwargs["bucket_cap_mb"] = self.args.ddp_bucket_cap_mb
        if self.args.ddp_broadcast_buffers is not None:
            ddp_kwargs["broadcast_buffers"] = self.args.ddp_broadcast_buffers
        if self.args.ddp_static_graph is not None:
            ddp_kwargs["static_graph"] = self.args.ddp_static_graph

        args["kwargs_handlers"] = [DistributedDataParallelKwargs(**ddp_kwargs)]

        # We defer compatibility checks to accelerator
        if self.args.parallelism_config is not None:
            min_accelerate_version = "1.12.0"
            if not is_accelerate_available(min_accelerate_version):
                raise ImportError(
                    f"ParallelismConfig requires accelerate>={min_accelerate_version}). Please upgrade accelerate to use this feature."
                )
            args["parallelism_config"] = self.args.parallelism_config

        if getattr(self.model, "tp_size", None) is not None and self.model.tp_size > 1:
            if self.args.parallelism_config is None:
                if is_accelerate_available("1.12.0"):
                    if self.args.parallelism_config is None:
                        from accelerate import ParallelismConfig

                        args["parallelism_config"] = ParallelismConfig(tp_size=self.model.tp_size)
                else:
                    raise ValueError("Requires accelerate>1.12.0 to use Tensor Parallelism.")
            elif args["parallelism_config"].tp_size != self.model.tp_size:
                args["parallelism_config"].tp_size = self.model.tp_size

        if is_accelerate_available("1.2.0"):
            # it we don't have the correct version, we will rely on env var instead that were set in TrainingArguments
            from accelerate.utils import TorchDynamoPlugin

            dynamo_plugin = TorchDynamoPlugin(
                backend=self.args.torch_compile_backend, mode=self.args.torch_compile_mode
            )
            args["dynamo_plugin"] = dynamo_plugin

        return args