def _progress_remaining_engine(self) -> bool:
        state = self.state
        assert self.old_dp_group is not None and self.old_dp_store is not None

        if state == ScaleDownRemainingEngineState.PREPARE:
            self.state = ScaleDownRemainingEngineState.EPLB_RESHUFFLE
            self.old_dp_store.add("eep_barrier_engine_count", 1)
            return True

        elif state == ScaleDownRemainingEngineState.EPLB_RESHUFFLE:
            if (
                int(self.old_dp_store.get("eep_barrier_engine_count"))
                < self.old_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=False, barrier_name="eplb_reshuffle"
            ):
                return False
            if self.old_dp_group.rank() == 0:
                self.old_dp_store.delete_key("eep_barrier_engine_count")
            self._eplb_reshuffle_before_scale_down()
            self.state = ScaleDownRemainingEngineState.SWITCH_AND_PREPARE
            # NOTE(yongji): currently, after EPLB reshuffle
            # that redistributes experts to remaining workers, workers
            # to be removed will immediately initiate shutdown;
            # existing workers can no longer execute forward steps using
            # the old setup. In the future, we may keep
            # the removing workers alive a bit longer,
            # e.g., to drain in-batch requests.
            self._create_standby_groups()
            self._switch_and_prepare()
            self._update_parallel_config()
            self.state = ScaleDownRemainingEngineState.COMPLETE
            return True

        else:
            assert self.state == ScaleDownRemainingEngineState.COMPLETE
            return True