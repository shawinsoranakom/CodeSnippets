def _progress_new_engine(self) -> bool:
        state = self.state
        assert self.new_dp_group is not None and self.new_dp_store is not None

        if state == ScaleUpNewEngineState.PRE_KV_INIT:
            self.engine_core._eep_send_engine_core_notification(
                EEPNotificationType.NEW_CORE_ENGINES_WEIGHTS_INIT_READY
            )
            self.model_executor.collective_rpc(
                "elastic_ep_execute", args=("receive_weights",)
            )
            self.engine_core.available_gpu_memory_for_kv_cache = (
                ParallelConfig.sync_kv_cache_memory_size(self.new_dp_group, -1)
            )
            self.model_executor.collective_rpc(
                "elastic_ep_execute", args=("prepare_new_worker",)
            )
            self.state = ScaleUpNewEngineState.PREPARE
            return True

        elif state == ScaleUpNewEngineState.PREPARE:
            tensor = torch.tensor([0, 0, 0], dtype=torch.int32, device="cpu")
            torch.distributed.all_reduce(
                tensor,
                op=torch.distributed.ReduceOp.MAX,
                group=self.new_dp_group,
            )
            data = tensor.tolist()
            self.engine_core.engines_running = bool(data[0])
            self.engine_core.current_wave = int(data[1])
            self.engine_core.step_counter = int(data[2])
            self.state = ScaleUpNewEngineState.EPLB_RESHUFFLE
            self.new_dp_store.add("eep_barrier_engine_count", 1)
            return True

        elif state == ScaleUpNewEngineState.EPLB_RESHUFFLE:
            if (
                int(self.new_dp_store.get("eep_barrier_engine_count"))
                < self.new_dp_group.size()
            ):
                return False
            if not self._staged_barrier(
                use_new_group=True, barrier_name="eplb_reshuffle"
            ):
                return False
            assert self.new_dp_group.rank() > 0
            self._eplb_reshuffle()
            self.state = ScaleUpNewEngineState.COMPLETE
            return True

        else:
            assert self.state == ScaleUpNewEngineState.COMPLETE
            return True