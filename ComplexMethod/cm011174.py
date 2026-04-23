def _pre_fw_hook(self, module: nn.Module, inputs: Any) -> None:
        # This is installed as a pre-fwd user hook with ``ModTracker.`` Based on the following cases we
        # set the state and capture the memory snapshot for the module.
        # Case 1: If the module is not in the ``memory_tracking`` dictionary, we track the parameters, buffers,
        #         input and output memory of the module. Create a new ``_ModMemStats`` instance for the module
        #         and add it to the ``memory_tracking`` dictionary.
        # Case 2: If the module is already in the ``memory_tracking`` dictionary and we are in backward, this means
        #         we are in the AC region. We check if this is the top most module in the AC region. If it is,
        #         we store a weak reference and set the flag ``_in_ac`` to True.
        # Case 3: If the module is already in the ``memory_tracking`` dictionary and we are in forward, this means
        #         this module is called for the second time. If it is a root module, that means we are in the next
        #         iteration and we error out. If it is not a root module, that means it's a submodule that is being
        #         used multiple times in the same iteration, which we allow and track.
        # For Case 1 and 3, we also initialize the ``local_peak`` and ``PEAK_FW`` snapshot for the module.
        mod_name = self._mod_tracker.get_known_fqn(module)
        if mod_name is None:
            raise AssertionError
        if module not in self.memory_tracking:
            mod_stats = _ModMemStats(mod_name)
            param_mem, buffer_mem = self._track_module_params_and_buffers(
                module, install_grad_hooks=True
            )
            input_mem = self._track_inputs_or_outputs(inputs)
            mod_stats.parameter_mem = param_mem
            mod_stats.buffer_mem = buffer_mem
            mod_stats.input_mem = input_mem
            self.memory_tracking[module] = mod_stats
            state = _ModState.PRE_FW

        elif self._mod_tracker.is_bw:
            mod_stats = self.memory_tracking[module]
            state = _ModState.PRE_FW_AC
            if self._ac_mod is None:
                self._ac_mod = weakref.ref(module)
                self._in_ac = True
        else:
            parents = set(self._mod_tracker.parents) - {mod_name}
            if len(parents) == 1 and "Global" in parents:
                raise NotImplementedError(
                    "MemTracker does not support memory tracking for multiple iterative calls."
                    " Either use ``reset_mod_stats`` to clear module memory stats for the previous iteration"
                    " or file a github issue if you need this feature."
                )
            mod_stats = self.memory_tracking[module]
            state = _ModState.PRE_FW
            input_mem = self._track_inputs_or_outputs(inputs)
            mod_stats.mod_fqn = mod_name
            mod_stats.input_mem = input_mem

        mem_snapshot = self.get_tracker_snapshot()
        if state == _ModState.PRE_FW:
            mod_stats.local_peak = {
                dev: dev_snap[_TOTAL_KEY] for dev, dev_snap in mem_snapshot.items()
            }
            mod_stats.snapshots.setdefault(_ModState.PEAK_FW, []).append(mem_snapshot)
        mod_stats.snapshots.setdefault(state, []).append(deepcopy(mem_snapshot))