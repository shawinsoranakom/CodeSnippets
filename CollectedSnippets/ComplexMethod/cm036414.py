def test_streaming_e2e_lifecycle(self):
        """
        Comprehensive integration test covering complete streaming request lifecycle
        including scheduler state management and aliasing bug prevention.

        FULL LIFECYCLE:
        ================
        CYCLE 1 (Initial Decode):
        1. Add streaming request (seq_id=0) with prompt tokens [1,2,3]
        2. Schedule() creates NewRequestData with prompt_token_ids
        3. Model runner caches this prompt_token_ids reference (simulated)
        4. Model executes and generates output token 10
        5. update_from_output() appends token 10 to request._all_token_ids
        6. Request transitions to RUNNING state

        CYCLE 2 (Continue Decode):
        7. Schedule() again - request is now in scheduled_cached_reqs (not new)
        8. Model runner uses CACHED state to calculate num_tokens
        9. Model generates output token (STOP_TOKEN)
        10. update_from_output() appends STOP_TOKEN to request._all_token_ids
        11. Request transitions to WAITING_FOR_STREAMING_REQ

        CYCLE 3 (New Streaming Request):
        12. Add new streaming request (seq_id=1) with prompt tokens [4,5]
        13. Scheduler merges into session, creates NewRequestData again
        14. Model runner caches new prompt_token_ids reference
        15. Verify cached state from Cycle 1 wasn't corrupted by mutations

        CRITICAL BUG PREVENTION:
        ========================
        Without .copy() in _create_new_request_data():
        - Cycle 1 Step 3: cached_state["prompt_token_ids"] aliases
            request._all_token_ids
        - Cycle 1 Step 5: When appending token 10, cached state mutates:
            [1,2,3] -> [1,2,3,10]
        - Cycle 2 Step 8: num_tokens = len([1,2,3,10]) + len([10])
            = 5 (WRONG! Should be 4)
        - Cycle 2: Discard logic would see seq_lens=4 < num_tokens=5
            -> INCORRECTLY DISCARDS

        With .copy() in _create_new_request_data():
        - Cycle 1 Step 3: cached_state["prompt_token_ids"] is independent copy
        - Cycle 1 Step 5: Only request._all_token_ids mutates, cached stays [1,2,3]
        - Cycle 2 Step 8: num_tokens = len([1,2,3]) + len([10]) = 4 (CORRECT)
        - Cycle 2: Discard logic works correctly
        """
        scheduler = create_scheduler()

        # ═══════════════════════════════════════════════════════════════════
        # CYCLE 1: Initial Request Scheduling and First Decode
        # ═══════════════════════════════════════════════════════════════════

        session = DummyRequest(
            request_id="session",
            prompt_token_ids=[1, 2, 3],
        )
        scheduler.add_request(session)

        # Step 2: Schedule creates NewRequestData
        scheduler_output_cycle1 = scheduler.schedule()

        # Verify request is in scheduled_new_reqs (first time scheduling)
        assert len(scheduler_output_cycle1.scheduled_new_reqs) == 1
        new_req_data_cycle1 = scheduler_output_cycle1.scheduled_new_reqs[0]
        assert new_req_data_cycle1.prompt_token_ids == [1, 2, 3]
        assert (
            scheduler_output_cycle1.num_scheduled_tokens[session.request_id] == 3
        )  # [1, 2, 3]
        assert (
            session.request_id
            not in scheduler_output_cycle1.scheduled_cached_reqs.req_ids
        )

        # Step 3: Simulate model runner caching the prompt_token_ids
        # This simulates gpu_model_runner.py:706-720 CachedRequestState creation
        # The model runner makes a copy of prompt_token_ids when creating
        # CachedRequestState
        cached_state_cycle1 = {
            "req_id": session.request_id,
            "prompt_token_ids": list(
                new_req_data_cycle1.prompt_token_ids
            ),  # Explicit copy
            "output_token_ids": [],
            "num_computed_tokens": 0,
        }

        # Store original for verification
        original_cached_prompt_cycle1 = cached_state_cycle1["prompt_token_ids"].copy()

        # Step 4-5: Model execution generates token, scheduler updates request
        output_token_1 = 10
        cached_state_cycle1["output_token_ids"].append(output_token_1)

        mro_cycle1 = ModelRunnerOutput(
            req_ids=[session.request_id],
            req_id_to_index={session.request_id: 0},
            sampled_token_ids=[[output_token_1]],
            logprobs=None,
            prompt_logprobs_dict={session.request_id: None},
            pooler_output=[],
        )
        session.num_computed_tokens = len(session.prompt_token_ids)
        eco_dict_cycle1 = scheduler.update_from_output(
            scheduler_output_cycle1, mro_cycle1
        )

        # Step 6: Verify request state after Cycle 1
        eco_cycle1 = eco_dict_cycle1[session.client_index].outputs[0]
        assert eco_cycle1.finish_reason is None  # Not stopped yet
        assert session.status == RequestStatus.RUNNING
        assert session in scheduler.running
        assert session._all_token_ids == [1, 2, 3, 10]  # Mutation happened here

        # CRITICAL ASSERTION: Cached prompt_token_ids must NOT have changed
        assert (
            cached_state_cycle1["prompt_token_ids"] == original_cached_prompt_cycle1
        ), (
            f"ALIASING BUG DETECTED in Cycle 1! "
            f"cached_state['prompt_token_ids'] was mutated from "
            f"{original_cached_prompt_cycle1} to "
            f"{cached_state_cycle1['prompt_token_ids']}. "
            f"This means _create_new_request_data() didn't call .copy()!"
        )
        assert cached_state_cycle1["prompt_token_ids"] is not session._all_token_ids, (
            "ALIASING BUG! cached_state['prompt_token_ids'] is the same object as "
            "session._all_token_ids. They must be independent copies."
        )

        # ═══════════════════════════════════════════════════════════════════
        # CYCLE 2: Continue Decoding (Using Cached State)
        # ═══════════════════════════════════════════════════════════════════

        # Step 7: Schedule again - now request uses cached state
        scheduler_output_cycle2 = scheduler.schedule()

        # Verify request is NOT in scheduled_new_reqs (already cached)
        assert not scheduler_output_cycle2.scheduled_new_reqs
        assert (
            session.request_id in scheduler_output_cycle2.scheduled_cached_reqs.req_ids
        )
        assert (
            scheduler_output_cycle2.num_scheduled_tokens[session.request_id] == 1
        )  # Only the output token [10]

        # Step 8: Calculate num_tokens like gpu_model_runner.py:1284 does
        # This is where the bug would manifest!
        num_tokens_cycle2 = len(cached_state_cycle1["prompt_token_ids"]) + len(
            cached_state_cycle1["output_token_ids"]
        )

        # CRITICAL ASSERTION: num_tokens must be correct (3 prompt + 1 output = 4)
        # Without .copy(), cached_state["prompt_token_ids"] would be [1,2,3,10]
        # and num_tokens would incorrectly be 5, causing the discard bug
        expected_num_tokens_cycle2 = 4
        assert num_tokens_cycle2 == expected_num_tokens_cycle2, (
            f"DISCARD BUG WOULD TRIGGER! num_tokens calculation is wrong. "
            f"Expected {expected_num_tokens_cycle2}, got {num_tokens_cycle2}. "
            f"cached_state['prompt_token_ids'] = "
            f"{cached_state_cycle1['prompt_token_ids']} (should be [1,2,3], not [1,2,3,"
            f"10]). Without .copy(), this would be 5 = len([1,2,3,10]) + len([10]). "
            f"Discard logic would see: seq_lens={session.num_computed_tokens} "
            f"< num_tokens={num_tokens_cycle2}, triggering incorrect discard!"
        )

        # Step 9-10: Model generates STOP_TOKEN, scheduler updates
        output_token_2 = STOP_TOKEN
        cached_state_cycle1["output_token_ids"].append(output_token_2)

        mro_cycle2 = ModelRunnerOutput(
            req_ids=[session.request_id],
            req_id_to_index={session.request_id: 0},
            sampled_token_ids=[[output_token_2]],
            logprobs=None,
            prompt_logprobs_dict={session.request_id: None},
            pooler_output=[],
        )
        eco_dict_cycle2 = scheduler.update_from_output(
            scheduler_output_cycle2, mro_cycle2
        )

        # Step 11: Verify request transitioned to WAITING_FOR_STREAMING_REQ
        eco_cycle2 = eco_dict_cycle2[session.client_index].outputs[0]
        assert eco_cycle2.finish_reason == FinishReason.STOP
        assert session.status == RequestStatus.WAITING_FOR_STREAMING_REQ
        assert session in scheduler.waiting
        assert session._all_token_ids == [1, 2, 3, 10, STOP_TOKEN]

        # CRITICAL ASSERTION: Cached prompt_token_ids STILL must not have changed
        assert cached_state_cycle1["prompt_token_ids"] == [1, 2, 3], (
            f"ALIASING BUG DETECTED in Cycle 2! "
            f"cached_state['prompt_token_ids'] = "
            f"{cached_state_cycle1['prompt_token_ids']} (should still be [1,2,3]). "
            f"Mutations from update_from_output() leaked through!"
        )

        # ═══════════════════════════════════════════════════════════════════
        # CYCLE 3: New Streaming Request (Session Continuation)
        # ═══════════════════════════════════════════════════════════════════

        # Step 12: Add new streaming request with seq_id=1
        new_request = DummyRequest(
            request_id="session",
            prompt_token_ids=[4, 5],
        )
        scheduler.add_request(new_request)

        # With the new streaming API, when session is in WAITING_FOR_STREAMING_REQ,
        # the update is applied directly via _update_request_as_session (not queued).
        # The session status becomes WAITING after the update is applied.
        assert session.status == RequestStatus.WAITING

        # Step 13: Scheduler schedules the updated session
        scheduler_output_cycle3 = scheduler.schedule()

        # Verify scheduler created NewRequestData with merged prompt_token_ids
        assert len(scheduler_output_cycle3.scheduled_new_reqs) == 1
        assert (
            scheduler_output_cycle3.scheduled_new_reqs[0].prompt_token_ids
            == session.prompt_token_ids
        )
        assert (
            scheduler_output_cycle3.num_scheduled_tokens[session.request_id] == 2
        )  # Only new tokens [4, 5]
        # Computed output tokens are kept (become part of prompt), only the
        # final uncomputed sampled token (STOP_TOKEN) is discarded
        assert session._all_token_ids == [1, 2, 3, 10, 4, 5]
        assert session.prompt_token_ids == [1, 2, 3, 10, 4, 5]  # Includes kept output
        assert session._output_token_ids == []  # Output tokens are cleared

        # Step 14: Model runner caches NEW prompt_token_ids reference
        # The model runner makes a copy of prompt_token_ids when creating
        # CachedRequestState
        new_req_data_cycle3 = scheduler_output_cycle3.scheduled_new_reqs[0]
        cached_state_cycle3 = {
            "req_id": session.request_id,
            "prompt_token_ids": list(
                new_req_data_cycle3.prompt_token_ids
            ),  # Explicit copy
            "output_token_ids": [],
            "num_computed_tokens": session.num_computed_tokens,
        }

        # Step 15: FINAL CRITICAL VERIFICATION
        # The old cached state from Cycle 1 must still be unchanged
        assert cached_state_cycle1["prompt_token_ids"] == [1, 2, 3], (
            f"PERSISTENT ALIASING BUG! Even after new scheduling cycle, "
            f"old cached_state was mutated to "
            f"{cached_state_cycle1['prompt_token_ids']}. This proves the aliasing bug "
            f"exists!"
        )

        # The new cached state must be independent
        assert cached_state_cycle3["prompt_token_ids"] is not session._all_token_ids, (
            "ALIASING BUG in Cycle 3! Cached state is aliased to _all_token_ids."
        )

        # Both cached states must be independent of each other
        assert (
            cached_state_cycle1["prompt_token_ids"]
            is not cached_state_cycle3["prompt_token_ids"]
        ), "Cached states from different cycles should be independent objects."