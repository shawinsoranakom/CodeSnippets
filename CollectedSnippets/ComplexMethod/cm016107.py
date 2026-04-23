def deepcopy_and_maybe_parallelize(self, model):
        model = self.deepcopy_model(model)
        if self.args.ddp:
            if not torch.distributed.is_available():
                raise AssertionError(
                    "Can't use DDP without a distributed enabled build"
                )
            from torch.nn.parallel import DistributedDataParallel as DDP

            model = DDP(model, find_unused_parameters=True)
        elif self.args.fsdp:
            if not torch.distributed.is_available():
                raise AssertionError(
                    "Can't use FSDP without a distributed enabled build"
                )
            from torch.distributed.fsdp import (
                FullyShardedDataParallel as FSDP,
                MixedPrecision,
            )

            if self.args.float16:
                dtype = torch.float16
            elif self.args.bfloat16:
                dtype = torch.bfloat16
            else:
                dtype = torch.float32

            mp_policy = MixedPrecision(
                param_dtype=dtype,
                # Gradient communication precision.
                reduce_dtype=dtype,
                # Buffer precision.
                buffer_dtype=dtype,
            )

            model = FSDP(
                model,
                use_orig_params=True,
                device_id=torch.cuda.current_device()
                if self.args.devices[-1] == "cuda"
                else None,
                mixed_precision=mp_policy,
                limit_all_gathers=True,
                auto_wrap_policy=self.get_fsdp_auto_wrap_policy(self.args.only),
            )
        return model