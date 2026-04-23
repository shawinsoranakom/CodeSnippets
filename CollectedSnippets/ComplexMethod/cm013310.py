def _profiler_test_with_rpc(
        self,
        rpc_exec_mode,
        func,
        args,
        use_record_function=False,
        dst=None,
        kineto_profile=False,
    ):
        dst = dst if dst is not None else (self.rank + 1) % self.world_size

        # only run profiler on rank 1.
        p = _profile if not kineto_profile else torch.profiler.profile  # kineto
        if self.rank == 1:
            with p() as prof:
                record_function_ctx_mgr = (
                    contextlib.nullcontext()
                    if not use_record_function
                    else torch.autograd.profiler.record_function("foo")
                )
                with record_function_ctx_mgr:
                    if rpc_exec_mode == RPCExecMode.SYNC:
                        rpc.rpc_sync(worker_name(dst), func, args=args)
                    elif rpc_exec_mode == RPCExecMode.ASYNC:
                        fut = rpc.rpc_async(worker_name(dst), func, args=args)
                        if kineto_profile:
                            # Ensure multiple async RPCs don't cause issues.
                            # Would have raised
                            # "RuntimeError: Cannot call
                            # RemoteProfilerManager::setCurrentKey when current
                            # key is already set." error if RPC profiling was
                            # not disabled properly for kineto.
                            fut2 = rpc.rpc_async(worker_name(dst), func, args=args)
                            fut2.wait()
                        fut.wait()
                    else:
                        self.assertTrue(rpc_exec_mode == RPCExecMode.REMOTE)
                        rref = rpc.remote(worker_name(dst), func, args=args)
                        rref.to_here()
                        # To avoid flakiness, wait for the RRef to be profiled. This
                        # means that we received the acknowledgement of successful
                        # creation on the owner and ran the callbacks responsible
                        # for recording the profiling event.
                        rref._get_profiling_future().wait()

            events = prof.function_events if not kineto_profile else prof.events()
            if kineto_profile:
                # RPC profiling is disabled so there should be no rpc related
                # events.
                with self.assertRaises(IndexError):
                    get_function_event(events, rpc_exec_mode.value)

                return

            rpc_event = get_function_event(events, rpc_exec_mode.value)
            # verify Node ID for this rpc event.
            self.assertEqual(rpc_event.node_id, self.rank)
            # Ensure recording of remote events.
            remote_events = {event for event in events if event.node_id == dst} - {
                rpc_event
            }
            self.assertGreaterEqual(len(remote_events), 1)
            for remote_event in remote_events:
                self.assertEqual(remote_event.node_id, dst)

            if use_record_function:
                scope_event = get_function_event(events, "foo")
                # Since RPC call is within the scope, its CPU interval should be
                # contained within foo's interval.
                self.assertLessEqual(
                    scope_event.time_range.start, rpc_event.time_range.start
                )
                self.assertGreaterEqual(
                    scope_event.time_range.end, rpc_event.time_range.end
                )
            # the sender, dest worker, function run, and type of RPC should all
            # be recorded.
            self_worker_name = worker_name(self.rank)
            dst_worker_name = worker_name(dst)
            self.check_profiling_info(
                self_worker_name, dst_worker_name, func, rpc_event, rpc_exec_mode
            )
            if use_record_function:
                # verify order by ensuring that the outer context comes
                # before the rpc event.
                foo_event_ix = next(
                    i for i, event in enumerate(events) if "foo" in event.name
                )
                rpc_event_idx = next(
                    i
                    for i, event in enumerate(events)
                    if rpc_exec_mode.value in event.name
                )
                self.assertLess(foo_event_ix, rpc_event_idx)