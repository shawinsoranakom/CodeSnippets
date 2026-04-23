def unscale_(self, optimizer: torch.optim.Optimizer) -> None:
        if not self._enabled:
            return

        self._check_scale_growth_tracker("unscale_")

        optimizer_state = self._per_optimizer_states[id(optimizer)]

        if optimizer_state["stage"] is OptState.UNSCALED:
            raise RuntimeError(
                "unscale_() has already been called on this optimizer since the last update()."
            )
        elif optimizer_state["stage"] is OptState.STEPPED:
            raise RuntimeError("unscale_() is being called after step().")

        # FP32 division can be imprecise for certain compile options, so we carry out the reciprocal in FP64.
        if self._scale is None:
            raise AssertionError("Expected _scale to be initialized, got None")
        inv_scale = self._scale.double().reciprocal().float()
        found_inf = torch.full(
            (1,), 0.0, dtype=torch.float32, device=self._scale.device
        )

        optimizer_state["found_inf_per_device"] = self._unscale_grads_(
            optimizer, inv_scale, found_inf, True
        )
        optimizer_state["stage"] = OptState.UNSCALED

        # Synchronize the detected inf across the ranks
        optimizer_state = self._per_optimizer_states[id(optimizer)]
        works = []
        found_inf_on_cpus = []
        found_inf_on_devices = []

        for found_inf in optimizer_state["found_inf_per_device"].values():
            if self._device != "cpu" and found_inf.device.type == "cpu":
                found_inf_on_cpus.append(found_inf)
                found_inf_on_device = found_inf.to(self._device)
                found_inf_on_devices.append(found_inf_on_device)
                works.append(
                    dist.all_reduce(
                        found_inf_on_device, async_op=True, group=self.process_group
                    )
                )
            else:
                works.append(
                    dist.all_reduce(found_inf, async_op=True, group=self.process_group)
                )
        for work in works:
            work.wait()
        if found_inf_on_cpus:
            torch._foreach_copy_(found_inf_on_cpus, found_inf_on_devices)