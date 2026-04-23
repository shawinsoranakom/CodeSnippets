def test_prefill_tp_size_greater_than_decode_tp_size_mla(
        self, default_vllm_config, dist_init
    ):
        """
        Verify remote TP > local TP handshake succeeds with different
        remote configurations for an MLA model.
        """
        vllm_config = create_vllm_config()
        d_tp_size = 1
        p_tp_size = 2

        # Build two separate connectors/workers to emulate P TP=2 ranks.
        conn_p0 = NixlConnector(
            vllm_config, KVConnectorRole.WORKER, make_kv_cache_config(block_size=16)
        )
        conn_p1 = NixlConnector(
            vllm_config, KVConnectorRole.WORKER, make_kv_cache_config(block_size=16)
        )
        conn_p0.connector_worker = FakeNixlConnectorWorker(
            vllm_config, conn_p0.engine_id, hand_shake_latency=0
        )
        conn_p1.connector_worker = FakeNixlConnectorWorker(
            vllm_config, conn_p1.engine_id, hand_shake_latency=0
        )

        # Force P world size to 2 for both workers and emulate distinct tp_ranks.
        # Also enable MLA path so that expected_finished_count is updated.
        for rank, worker in enumerate(
            (conn_p0.connector_worker, conn_p1.connector_worker)
        ):
            worker.world_size = p_tp_size
            worker.transfer_topo.tp_size = p_tp_size
            worker.tp_rank = rank
            worker.use_mla = True

        req_id = "req-ep-dp2-p0"
        now = time.perf_counter()
        # Register a request on P that is waiting for consumers to read
        # (both workers track it).
        conn_p0.connector_worker._reqs_to_send[req_id] = now + 10.0
        conn_p0.connector_worker._reqs_to_process.add(req_id)
        conn_p1.connector_worker._reqs_to_send[req_id] = now + 10.0
        conn_p1.connector_worker._reqs_to_process.add(req_id)

        # Simulate a read notification coming from D with (tp=1, dp=2).
        notif = f"{req_id}:{d_tp_size}".encode()
        # D0-0->P0 notif
        conn_p0.connector_worker.nixl_wrapper.get_new_notifs = lambda: {
            "agent": [notif]
        }  # type: ignore[method-assign]
        conn_p1.connector_worker.nixl_wrapper.get_new_notifs = lambda: {
            "agent": [notif]
        }  # type: ignore[method-assign]

        # Trigger notification processing via get_finished().
        done_sending0, _ = conn_p0.get_finished(finished_req_ids=set())
        done_sending1, _ = conn_p1.get_finished(finished_req_ids=set())
        assert req_id in done_sending0 and req_id in done_sending1

        # E2E aggregation: ensure the aggregated output marks the request
        # as finished using the connector's expected_finished_count.
        from vllm.v1.outputs import KVConnectorOutput, ModelRunnerOutput

        aggregator = KVOutputAggregator.from_connector(conn_p0, world_size=2)

        out0 = ModelRunnerOutput(
            req_ids=[req_id],
            req_id_to_index={req_id: 0},
            sampled_token_ids=[[0]],
            logprobs=None,
            prompt_logprobs_dict={},
            pooler_output=[None],
            kv_connector_output=KVConnectorOutput(
                finished_sending=done_sending0,
                finished_recving=None,
            ),
        )
        out1 = ModelRunnerOutput(
            req_ids=[req_id],
            req_id_to_index={req_id: 0},
            sampled_token_ids=[[0]],
            logprobs=None,
            prompt_logprobs_dict={},
            pooler_output=[None],
            kv_connector_output=KVConnectorOutput(
                finished_sending=done_sending1,
                finished_recving=None,
            ),
        )
        aggregated = aggregator.aggregate([out0, out1], output_rank=0)
        assert aggregated.kv_connector_output is not None
        assert aggregated.kv_connector_output.finished_sending == {req_id}

        # Producers cleaned up state for the finished request.
        assert req_id not in conn_p0.connector_worker._reqs_to_send
        assert req_id not in conn_p0.connector_worker._reqs_to_process
        assert req_id not in conn_p1.connector_worker._reqs_to_send
        assert req_id not in conn_p1.connector_worker._reqs_to_process