def aggregate(
        self, outputs: list[ModelRunnerOutput | None], output_rank: int = 0
    ) -> ModelRunnerOutput | None:
        if not outputs[output_rank]:
            return None

        # Aggregate kv_connector_output from all workers

        def update_finished_set(
            req_ids: set[str] | None,
            remaining_count_dict: dict[str, int],
            finished_set: set[str],
        ) -> None:
            for req_id in req_ids or ():
                remaining_count = remaining_count_dict.get(
                    req_id, self._expected_finished_count
                )
                remaining_count_dict[req_id] = remaining_count - 1
                if remaining_count_dict[req_id] == 0:
                    finished_set.add(req_id)
                    del remaining_count_dict[req_id]

        finished_sending = set[str]()
        finished_recving = set[str]()
        aggregated_kv_connector_stats = None
        aggregated_kv_connector_worker_meta = None
        combined_kv_cache_events = None
        invalid_block_ids = set[int]()
        for model_runner_output in outputs:
            assert model_runner_output is not None
            kv_output = model_runner_output.kv_connector_output
            if not kv_output:
                continue
            # Allow the worker to dynamically update the expected number of
            # finished sending/recving for new requests.
            if (
                kv_output.expected_finished_count > 0
                and kv_output.expected_finished_count != self._expected_finished_count
            ):
                logger.debug(
                    "Expected finished requests updated from %d to %d",
                    self._expected_finished_count,
                    kv_output.expected_finished_count,
                )
                self._expected_finished_count = kv_output.expected_finished_count

            update_finished_set(
                kv_output.finished_sending, self._send_remaining_count, finished_sending
            )
            update_finished_set(
                kv_output.finished_recving, self._recv_remaining_count, finished_recving
            )

            # Aggregate kv_connector_stats from all workers.
            if aggregated_kv_connector_stats is None:
                # Use the first worker's kv_connector_stats as accumulator.
                aggregated_kv_connector_stats = kv_output.kv_connector_stats
            elif kv_connector_stats := kv_output.kv_connector_stats:
                if aggregated_kv_connector_stats is None:
                    aggregated_kv_connector_stats = kv_connector_stats
                else:
                    assert isinstance(
                        aggregated_kv_connector_stats, type(kv_connector_stats)
                    )
                    aggregated_kv_connector_stats = (
                        aggregated_kv_connector_stats.aggregate(kv_connector_stats)
                    )

            # Aggregate kv_connector_worker_meta from all workers.
            if aggregated_kv_connector_worker_meta is None:
                # Use the first worker's kv_connector_worker_meta as accumulator.
                aggregated_kv_connector_worker_meta = kv_output.kv_connector_worker_meta
            elif kv_connector_worker_meta := kv_output.kv_connector_worker_meta:
                aggregated_kv_connector_worker_meta = (
                    aggregated_kv_connector_worker_meta.aggregate(
                        kv_connector_worker_meta
                    )
                )

            # Combine kv_cache_events from all workers.
            if combined_kv_cache_events is None:
                # Use the first worker's kv_cache events as start event list.
                combined_kv_cache_events = kv_output.kv_cache_events
            elif kv_cache_events := kv_output.kv_cache_events:
                assert isinstance(
                    combined_kv_cache_events,
                    type(kv_cache_events),
                )
                worker_kv_cache_events = kv_cache_events.get_all_events()
                combined_kv_cache_events.add_events(worker_kv_cache_events)
                combined_kv_cache_events.increment_workers(1)

            invalid_block_ids |= kv_output.invalid_block_ids

        # select output of the worker specified by output_rank
        output = outputs[output_rank]

        assert output is not None
        output.kv_connector_output = KVConnectorOutput(
            finished_sending=finished_sending or None,
            finished_recving=finished_recving or None,
            kv_connector_stats=aggregated_kv_connector_stats or None,
            kv_cache_events=combined_kv_cache_events or None,
            kv_connector_worker_meta=aggregated_kv_connector_worker_meta or None,
            invalid_block_ids=invalid_block_ids,
            expected_finished_count=self._expected_finished_count,
        )

        return output