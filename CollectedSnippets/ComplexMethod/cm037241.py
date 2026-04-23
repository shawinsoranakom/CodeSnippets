def build_connector_meta(
        self,
        scheduler_output: SchedulerOutput,
    ) -> SimpleCPUOffloadMetadata:
        # --- Stores ---
        store_event = -1
        store_gpu, store_cpu, store_req_ids = self.prepare_store_specs(scheduler_output)
        if store_gpu:
            store_event = self._store_event_counter
            self._store_event_counter += 1
            self._store_event_to_blocks[store_event] = TransferMeta(
                store_gpu, store_cpu
            )
            if store_req_ids:  # For eager mode only, track req->blocks mapping
                self._store_event_to_reqs[store_event] = store_req_ids
                for req_id in store_req_ids:
                    store_state = self._reqs_to_store.get(req_id)
                    if store_state is not None:
                        store_state.store_events.add(store_event)

        # --- Loads ---
        load_event = -1
        load_gpu: list[int] = []
        load_cpu: list[int] = []
        load_req_ids: list[str] = []
        for req_id, load_state in self._reqs_to_load.items():
            if load_state.load_event is not None:
                continue
            assert load_state.transfer_meta is not None
            load_gpu.extend(load_state.transfer_meta.gpu_block_ids)
            load_cpu.extend(load_state.transfer_meta.cpu_block_ids)
            load_req_ids.append(req_id)
        if load_req_ids:
            load_event = self._load_event_counter
            self._load_event_counter += 1
            for req_id in load_req_ids:
                self._reqs_to_load[req_id].load_event = load_event
            self._load_event_to_reqs[load_event] = load_req_ids

        result = SimpleCPUOffloadMetadata(
            load_event=load_event,
            load_gpu_blocks=load_gpu,
            load_cpu_blocks=load_cpu,
            load_event_to_reqs=self._load_event_to_reqs,
            store_event=store_event,
            store_gpu_blocks=store_gpu,
            store_cpu_blocks=store_cpu,
            need_flush=bool(scheduler_output.preempted_req_ids),
        )
        return result