def _update_peak_stats(self, peak_state: _State) -> None:
        # We first capture the current memory snapshot of the current tracker state then,
        # We step through each of the modules we have tracked so far in ``memory_tracking``
        #  and check if it is currently active by querying ``_mod_tracker.parents``
        # If it is active, we update the per device peak memory usage for the module
        #  corresponding to the ``_State`` which can be ``PEAK_FW`` or ``PEAK_BW``.
        curr_snap = self._curr_mem_snap

        for mod_stats in self.memory_tracking.values():
            if mod_stats.mod_fqn in self._mod_tracker.parents:
                if peak_state in mod_stats.snapshots:
                    for dev, dev_snap in curr_snap.items():
                        if mod_stats.local_peak.get(dev, 0) < dev_snap[_TOTAL_KEY]:
                            mod_stats.local_peak[dev] = dev_snap[_TOTAL_KEY]
                            mod_stats.snapshots[peak_state][-1][dev] = deepcopy(
                                dev_snap
                            )

        for dev, dev_snap in curr_snap.items():
            if self._peak_mem.get(dev, 0) < dev_snap[_TOTAL_KEY]:
                self._peak_mem[dev] = dev_snap[_TOTAL_KEY]
                self._peak_mem_snap[dev] = deepcopy(dev_snap)