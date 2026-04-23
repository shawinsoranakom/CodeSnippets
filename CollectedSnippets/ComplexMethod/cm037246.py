def get_finished(
        self,
        finished_req_ids: set[str],
    ) -> tuple[set[str] | None, set[str] | None]:
        """Submit transfers and report completed events to the scheduler.

        Called after model execution. The manager only schedules stores for
        blocks whose KV data is confirmed computed, so we launch both loads
        and stores immediately — no deferral or cross-stream sync needed.

        Returns:
            tuple of (finished_sending, finished_recving).
            - finished_sending: always None (stores use worker metadata).
            - finished_recving: req_ids whose loads have completed.
        """
        # (1) Submit transfers
        metadata = self._connector_metadata
        if metadata is not None:
            # Launch loads (CPU->GPU).
            if metadata.load_cpu_blocks:
                self._backend.launch_copy(
                    metadata.load_cpu_blocks,
                    metadata.load_gpu_blocks,
                    is_store=False,
                    event_idx=metadata.load_event,
                    events_list=self._load_events,
                )
            # Launch stores (GPU->CPU).
            if metadata.store_gpu_blocks:
                self._backend.launch_copy(
                    metadata.store_gpu_blocks,
                    metadata.store_cpu_blocks,
                    is_store=True,
                    event_idx=metadata.store_event,
                    events_list=self._store_events,
                )

        # (2) Track completed transfer events
        finished_recving: set[str] = set()

        if self._pending_load_event_indices:
            load_wm = self._poll_stream_events(is_store=False)
            for j in [j for j in self._pending_load_event_indices if j <= load_wm]:
                self._pending_load_event_indices.discard(j)
                req_ids = (
                    metadata.load_event_to_reqs.get(j) if metadata is not None else None
                )
                if req_ids:
                    finished_recving.update(req_ids)

        if self._pending_store_event_indices:
            store_wm = self._poll_stream_events(is_store=True)
            for j in [j for j in self._pending_store_event_indices if j <= store_wm]:
                self._pending_store_event_indices.discard(j)
                self._completed_store_events[j] = 1

        return None, finished_recving or None