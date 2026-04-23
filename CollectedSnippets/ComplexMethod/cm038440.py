def _progress_existing_engine(self) -> bool:
        state = self.state
        assert self.old_dp_group is not None and self.old_dp_store is not None

        if state == ScaleUpExistingEngineState.WAIT_NEW_CORE_ENGINES_INIT:
            return False

        elif state == ScaleUpExistingEngineState.CREATE_STANDBY_GROUPS:
            # NOTE(yongji): wait for all existing workers to receive the request
            if (
                int(self.old_dp_store.get("eep_barrier_engine_count"))
                < self.old_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=False, barrier_name="create_standby_groups"
            ):
                return False
            if self.old_dp_group.rank() == 0:
                self.old_dp_store.delete_key("eep_barrier_engine_count")
            self._create_standby_groups()
            self.state = ScaleUpExistingEngineState.TRANSFER_EXPERT_MAPPING
            return True

        elif state == ScaleUpExistingEngineState.TRANSFER_EXPERT_MAPPING:
            self._transfer_expert_mapping()
            self.state = ScaleUpExistingEngineState.WAIT_NEW_CORE_ENGINES_WEIGHTS_INIT
            return True

        elif state == ScaleUpExistingEngineState.WAIT_NEW_CORE_ENGINES_WEIGHTS_INIT:
            return False

        elif state == ScaleUpExistingEngineState.TRANSFER_WEIGHTS:
            if (
                int(self.old_dp_store.get("eep_barrier_engine_count"))
                < self.old_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=False, barrier_name="transfer_weights"
            ):
                return False
            if self.old_dp_group.rank() == 0:
                self.old_dp_store.delete_key("eep_barrier_engine_count")
            self._transfer_weights()
            self.state = ScaleUpExistingEngineState.SYNC_KV_CACHE_MEMORY_SIZE
            return True

        elif state == ScaleUpExistingEngineState.SYNC_KV_CACHE_MEMORY_SIZE:
            self._sync_kv_cache_memory_size()
            self.state = ScaleUpExistingEngineState.SWITCH_AND_PREPARE
            return True

        elif state == ScaleUpExistingEngineState.SWITCH_AND_PREPARE:
            self._switch_and_prepare()
            self.state = ScaleUpExistingEngineState.EPLB_RESHUFFLE
            assert self.new_dp_store is not None
            self.new_dp_store.add("eep_barrier_engine_count", 1)
            return True

        elif state == ScaleUpExistingEngineState.EPLB_RESHUFFLE:
            assert self.new_dp_group is not None and self.new_dp_store is not None
            if (
                int(self.new_dp_store.get("eep_barrier_engine_count"))
                < self.new_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=True, barrier_name="eplb_reshuffle"
            ):
                return False
            if self.new_dp_group.rank() == 0:
                self.new_dp_store.delete_key("eep_barrier_engine_count")
            self._eplb_reshuffle()
            self.state = ScaleUpExistingEngineState.COMPLETE
            self._update_parallel_config()
            return True

        else:
            assert self.state == ScaleUpExistingEngineState.COMPLETE
            return True