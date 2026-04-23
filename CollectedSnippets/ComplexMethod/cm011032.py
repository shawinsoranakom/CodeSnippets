def init(
        self,
        module: nn.Module,
        ignored_modules: set[nn.Module],
        **kwargs,
    ) -> None:
        if self.has_initialized:
            return

        self.has_initialized = True
        self.module = module
        ignored_params = {p for m in ignored_modules for p in m.parameters()}
        for submodule in module.modules():
            if _is_fully_sharded(submodule):
                ignored_params.update(submodule.parameters())
        from torch.distributed.tensor.parallel.ddp import _localize_dtensor

        _localize_dtensor(module, ignored_params=ignored_params)
        self._collect_params(module, ignored_modules, ignored_params)

        if "device_id" in kwargs:
            # replicate() supports a small usability enhancement where
            # user can pass in device_id as a Union[int, torch.device] even for
            # CPU devices so users don't have to change code for CPU/GPU runs.
            # We derive the right device_ids to feed into DDP to support this.
            if kwargs["device_id"] is not None:
                device_id = kwargs["device_id"]
                # Convert to device_ids that DDP expects.
                if isinstance(device_id, torch.device) and device_id.type == "cpu":
                    # CPU modules receive device_ids None
                    kwargs["device_ids"] = None
                else:
                    # GPU modules expect device_ids=[cuda_device]
                    kwargs["device_ids"] = [device_id]
            else:
                kwargs["device_ids"] = None
            kwargs.pop("device_id")

        self._ddp = DistributedDataParallel(self._param_list, **kwargs)
        # Weakref to the DDP instance is currently only used for testing.
        replicate.state(self.module)._ddp_weakref = weakref.ref(self._ddp)