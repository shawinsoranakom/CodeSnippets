def _run_test_profiler_remote_events_profiled(self):
        # Tests that we can successfully invoke the profiler on a remote node,
        # and collect the remote events back in the local profiler.
        if self.rank != 1:
            return

        dst_ranks = [rank for rank in range(self.world_size) if rank != self.rank]
        for dst in dst_ranks:
            dst_worker = worker_name(dst)
            with _profile() as prof:
                fut = rpc.rpc_async(dst_worker, udf_with_torch_ops, args=())
                fut.wait()

            events = prof.function_events

            rpc_event = get_function_event(events, RPCExecMode.ASYNC.value)
            self.check_profiling_info(
                worker_name(self.rank),
                dst_worker,
                udf_with_torch_ops,
                rpc_event,
                RPCExecMode.ASYNC,
            )

            remote_events = {event.name: event for event in events if event.is_remote}
            rpc_profiling_key = _build_rpc_profiling_key(
                RPCExecMode.ASYNC,
                udf_with_torch_ops.__qualname__,
                worker_name(self.rank),
                worker_name(dst),
            )

            for expected_remote_event_name in EXPECTED_REMOTE_EVENTS:
                expected_key = (
                    rpc_profiling_key + REMOTE_OP_STR + expected_remote_event_name
                )
                self.assertTrue(expected_key in remote_events)
                remote_event = remote_events[expected_key]
                # Remote event should have a node ID corresponding to the worker
                # it ran on.
                self.assertEqual(remote_event.node_id, dst)

            # Validate order remote events show up in profiling output.
            def convert_remote_to_local(event_name):
                remote_op_key = rpc_profiling_key + REMOTE_OP_STR
                return event_name[event_name.find(remote_op_key) + len(remote_op_key) :]

            remote_events_list = [
                convert_remote_to_local(event.name)
                for event in events
                if convert_remote_to_local(event.name) in EXPECTED_REMOTE_EVENTS
            ]
            self.assertEqual(
                set(remote_events_list),
                set(EXPECTED_REMOTE_EVENTS),
                f"Mismatch between profiled events: {set(remote_events_list)} and expected events: {set(EXPECTED_REMOTE_EVENTS)}",
            )