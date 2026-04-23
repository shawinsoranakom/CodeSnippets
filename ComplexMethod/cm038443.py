def _progress_removing_engine(self) -> bool:
        state = self.state
        assert self.old_dp_group is not None and self.old_dp_store is not None

        if state == ScaleDownRemovingEngineState.PREPARE:
            self.state = ScaleDownRemovingEngineState.EPLB_RESHUFFLE
            self.old_dp_store.add("eep_barrier_engine_count", 1)
            return True

        if state == ScaleDownRemovingEngineState.EPLB_RESHUFFLE:
            if (
                int(self.old_dp_store.get("eep_barrier_engine_count"))
                < self.old_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=False, barrier_name="eplb_reshuffle"
            ):
                return False
            assert self.old_dp_group.rank() > 0
            self._eplb_reshuffle_before_scale_down()
            self._switch_and_remove()
            self.state = ScaleDownRemovingEngineState.COMPLETE
            self.engine_core._eep_send_engine_core_notification(
                EEPNotificationType.SHUTDOWN_COMPLETE
            )
            return True

        else:
            assert self.state == ScaleDownRemovingEngineState.COMPLETE
            return True