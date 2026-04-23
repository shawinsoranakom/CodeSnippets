def __torch_dispatch__(self, func, types, args=..., kwargs=None):  # type: ignore[no-untyped-def]
        # When running this mode with DTensor, ordinarily all modes will
        # run **before** subclasses get a chance to run.
        # Returning NotImplemented here gives us a chance to let DTensor
        # run and desugar into local tensor ops, before `MemTracker` sees them.
        if any(t == DTensor for t in types):
            return NotImplemented
        if (
            func is torch.ops._c10d_functional.wait_tensor.default
            and active_fake_mode()
        ):
            # N.B: This is a hacky way to override the Meta IMPL of wait_tensor. The original impl returns
            # a new tensor which does not happen in eager mode, when a wait_tensor is called.
            # pyrefly: ignore [unsupported-operation]
            res = args[0]
        else:
            res = func(*args, **kwargs or {})
        # If we are tracking an optimizer state, we use the optimizer reference type.
        # If we are in backward region and not in AC region, we use the backward reference type.
        # Else we use the forward reference type.
        if self._in_opt:
            reftype = _FSDPRefType.OPT
        elif self._mod_tracker.is_bw and not self._in_ac:
            reftype = _FSDPRefType.TEMP
        else:
            reftype = _FSDPRefType.ACT
        if func is c10d._allgather_base_.default and self._fsdp_state in [
            _FSDPState.PRE_FW,
            _FSDPState.PRE_BW,
        ]:
            # pyrefly: ignore [unsupported-operation]
            output_tensor = args[0]
            self._update_and_maybe_create_winfos(
                output_tensor,
                _FSDPRefType.ALL_GATHER,
                update_existing=True,
            )
        if (
            func is c10d._reduce_scatter_base_.default
            and self._fsdp_state == _FSDPState.POST_BW
        ):
            # pyrefly: ignore [unsupported-operation]
            input_tensor = args[1]
            self._update_and_maybe_create_winfos(
                input_tensor,
                _FSDPRefType.REDUCE_SCATTER,
                update_existing=True,
            )

        tree_map_only(torch.Tensor, partial(self._track, reftype), res)
        peak_state = (
            _FSDPModState.PEAK_BW if self._mod_tracker.is_bw else _FSDPModState.PEAK_FW
        )
        self._update_peak_stats(peak_state)
        return res