def _distribute_region(
        self, spec: DTensorSpec, generator: torch.Generator | None = None
    ):
        from torch.distributed._local_tensor import maybe_enable_local_tracker

        if local_tracker_context := maybe_enable_local_tracker(
            self._device.type, self.distribute_region_enabled, spec, generator
        ):
            with local_tracker_context:
                yield
            return

        # regular (non-LocalTensor) mode
        if generator is not None:
            # This is a little hacky, but for any user-passed generator, we store its state under a unique key,
            # not because we need to keep a copy of it but because its the easiest way to make it work with the
            # existing set/get APIs. We also ensure we remove it from rng_states after each _distribute_region.
            state = _PhiloxState(generator.get_state())
        else:
            state = _PhiloxState(self._get_device_state())

        if self.distribute_region_enabled:
            if self._device.type == "hpu":
                self._device_handle.set_rng_ctx("philox")
            old_offset = state.offset.clone()
            self._set_pre_op_offset(state, spec)
            with torch.random.fork_rng(
                devices=[self._device], device_type=self._device.type
            ):
                if self._device_handle is None:
                    raise AssertionError
                self._device_handle.set_rng_state(state.state)
                try:
                    yield  # execute the region code
                finally:
                    # update offset to synchronize among ranks
                    self._set_post_op_offset(state, spec, old_offset)
            if self._device.type == "hpu":
                self._device_handle.unset_rng_ctx("philox")
        else:
            yield

        if generator is not None:
            # ensure we (a) propagate the state advancement back to the user's RNG so its visible and impacts any future
            # usage of that RNG (dtensor or non-dtensor), (b) drop it from our own cache so that if the user updates
            # the seed value in their rng and uses it with DTensor again, we always use the latest value
            generator.set_state(state.state)
        else:
            self._set_device_state(state.state)