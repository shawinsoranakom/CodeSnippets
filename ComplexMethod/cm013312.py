def test_rpc_async_jit_profiled(self):
        # Tests that rpc_async calls made from within a TorchScript function are
        # profiled.
        if self.rank == 0:
            dst_rank = (self.rank + 1) % self.world_size
            dst_worker_name = worker_name(dst_rank)
            args = (torch.tensor([1, 1]), torch.tensor([2, 2]))
            kwargs = {}
            with _profile() as prof:
                script_rpc_async_call(dst_worker_name, args, kwargs)

            # Ensure rpc_async call is profiled
            function_events = prof.function_events
            qual_name = torch._jit_internal._qualified_name(two_args_two_kwargs)
            rpc_async_jit_event = [
                event
                for event in function_events
                if qual_name in event.name and event.node_id == self.rank
            ]
            self.assertEqual(len(rpc_async_jit_event), 1)
            rpc_async_jit_event = rpc_async_jit_event[0]
            profiled_name = _build_rpc_profiling_key(
                RPCExecMode.ASYNC_JIT,
                qual_name,
                worker_name(self.rank),
                dst_worker_name,
            )
            self.assertEqual(profiled_name, rpc_async_jit_event.name)
            remote_events = [event for event in function_events if event.is_remote]
            # All remote events should have taken place on dst_rank
            remote_event_node_ids = {
                remote_event.node_id for remote_event in remote_events
            }
            self.assertEqual(remote_event_node_ids, {dst_rank})
            # script_rpc_async_call invokes add operator
            # so we should see this as a remote event.
            remote_add = next(
                remote_event
                for remote_event in remote_events
                if "aten::add" in remote_event.name
            )
            remote_add_profiled_name = f"{profiled_name}#remote_op: aten::add"
            self.assertEqual(remote_add.name, remote_add_profiled_name)