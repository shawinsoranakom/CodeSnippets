def test_lmcache_kv_events_aggregation(self):
        """
        Test LMCacheKVEvents aggregation across TP ranks using
        KVOutputAggregator (used by MultiprocExecutor).
        """
        from vllm.distributed.kv_transfer.kv_connector.utils import KVOutputAggregator
        from vllm.v1.outputs import ModelRunnerOutput

        # Create KVOutputAggregator for 3 workers (simulating TP=3)
        aggregator = KVOutputAggregator(expected_finished_count=3)

        # Define common and unique events
        common_event = BlockStored(
            block_hashes=["hash_common"],
            parent_block_hash="parent_common",
            token_ids=[1, 2, 3],
            block_size=16,
            lora_id=None,
            medium="GPU",
            lora_name=None,
        )

        worker1_unique_event = BlockStored(
            block_hashes=["hash_worker1"],
            parent_block_hash="parent_w1",
            token_ids=[4, 5],
            block_size=16,
            lora_id=None,
            medium="GPU",
            lora_name=None,
        )

        worker2_unique_event = BlockStored(
            block_hashes=["hash_worker2"],
            parent_block_hash="parent_w2",
            token_ids=[6, 7],
            block_size=16,
            lora_id=None,
            medium="GPU",
            lora_name=None,
        )

        worker3_unique_event = BlockStored(
            block_hashes=["hash_worker3"],
            parent_block_hash="parent_w3",
            token_ids=[8, 9],
            block_size=16,
            lora_id=None,
            medium="GPU",
            lora_name=None,
        )

        # Create events for each worker
        # Worker 0: reports common event and its unique event
        worker0_events = LMCacheKVEvents(num_workers=1)
        worker0_events.add_events([common_event, worker1_unique_event])

        # Worker 1: reports common event and its unique event
        worker1_events = LMCacheKVEvents(num_workers=1)
        worker1_events.add_events([common_event, worker2_unique_event])

        # Worker 2: reports common event and its unique event
        worker2_events = LMCacheKVEvents(num_workers=1)
        worker2_events.add_events([common_event, worker3_unique_event])

        # Create ModelRunnerOutput instances for each worker
        worker_outputs = []
        for i, worker_events in enumerate(
            [worker0_events, worker1_events, worker2_events]
        ):
            output = ModelRunnerOutput(
                req_ids=[f"req_{i}"],
                req_id_to_index={f"req_{i}": 0},
                sampled_token_ids=[[123]],  # dummy token
                logprobs=None,
                prompt_logprobs_dict={},
                pooler_output=[None],
                kv_connector_output=KVConnectorOutput(
                    finished_sending=set([f"req_{i}_send"])
                    if i < 2
                    else None,  # Workers 0,1 finished sending
                    finished_recving=set([f"req_{i}_recv"])
                    if i > 0
                    else None,  # Workers 1,2 finished receiving
                    kv_cache_events=worker_events,
                ),
            )
            worker_outputs.append(output)

        # Use the real aggregation mechanism (like MultiprocExecutor.execute_model)
        aggregated_output = aggregator.aggregate(worker_outputs, output_rank=0)
        kv_cache_events = aggregated_output.kv_connector_output.kv_cache_events

        assert isinstance(kv_cache_events, LMCacheKVEvents)

        # After aggregation, events should be combined from all workers
        # The aggregator doesn't automatically aggregate events, so we need to call
        # aggregate() to get only common events
        kv_cache_events.aggregate()
        aggregated_events = kv_cache_events.get_all_events()

        # Only the common event should remain after aggregation
        # because it's the only event reported by all 3 workers
        assert len(aggregated_events) == 1
        assert aggregated_events[0] == common_event

        # Verify the common event properties
        assert aggregated_events[0].block_hashes == ["hash_common"]
        assert aggregated_events[0].parent_block_hash == "parent_common"
        assert aggregated_events[0].token_ids == [1, 2, 3]