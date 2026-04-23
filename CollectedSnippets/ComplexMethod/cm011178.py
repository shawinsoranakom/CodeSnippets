def inner(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> tuple[tuple[Unpack[_Ts]], dict[str, Any]]:
            self._fsdp_state = _FSDPState.PRE_FW
            mod_fqn = self._mod_tracker.get_known_fqn(fsdp_mod)
            if mod_fqn is None:
                raise AssertionError
            if fsdp_mod not in self.memory_tracking:
                mod_stat = _FSDPModMemStats(mod_fqn)
                self.memory_tracking[fsdp_mod] = mod_stat
                snapshot = self.get_tracker_snapshot()
                mod_stat.local_peak = {
                    dev: dev_snap[_TOTAL_KEY] for dev, dev_snap in snapshot.items()
                }
                mod_stat.snapshots.setdefault(_FSDPModState.PEAK_FW, []).append(
                    snapshot
                )
                mod_stat.snapshots.setdefault(_FSDPModState.BEF_PRE_FW, []).append(
                    deepcopy(snapshot)
                )
            elif not self._mod_tracker.is_bw:
                parents = self._mod_tracker.parents - {mod_fqn}
                if len(parents) == 1 and "Global" in parents:
                    raise NotImplementedError(
                        "FSDPMemTracker does not support memory tracking for multiple iterative calls."
                        " Either use ``reset_mod_stats`` to clear module memory stats for the previous iteration"
                        " or file a github issue if you need this feature."
                    )

            # pyrefly: ignore [bad-assignment]
            args, kwargs = orig_fsdp_state_pre_fw(*args, **kwargs)

            fsdp_state = fsdp_mod._get_fsdp_state()
            if fsdp_param_group := fsdp_state._fsdp_param_group:
                for fsdp_param in fsdp_param_group.fsdp_params:
                    self._update_and_maybe_create_winfos(
                        fsdp_param.unsharded_param,
                        _FSDPRefType.UNSHARDED_PARAM,
                    )
            mod_stat = self.memory_tracking[fsdp_mod]
            if self._mod_tracker.is_bw:
                state = _FSDPModState.PRE_FW_AC
                if self._ac_mod is None:
                    self._ac_mod = weakref.ref(fsdp_mod)
                    self._in_ac = True
            else:
                state = _FSDPModState.AFT_PRE_FW
            mod_stat.snapshots.setdefault(state, []).append(self.get_tracker_snapshot())
            self._fsdp_state = _FSDPState.FW
            # pyrefly: ignore [bad-return]
            return args, kwargs