def _run_rpc_profiling_async_function(self, device="cpu"):
        if self.rank != 1:
            return

        dst1 = worker_name((self.rank + 1) % self.world_size)
        dst2 = worker_name((self.rank + 2) % self.world_size)
        x = torch.ones(2)
        y = torch.ones(2)
        with _profile() as prof:
            ret = rpc.rpc_async(
                dst1, slow_async_add, args=(dst2, x, y, device), timeout=20
            )
            ret.wait()

        function_events = prof.function_events
        # slow_async_add resulted in an RPC from dst1 -> dst2, so this should be
        # recorded.
        key_prefix = _build_rpc_profiling_key(
            RPCExecMode.ASYNC, slow_async_add.__qualname__, worker_name(self.rank), dst1
        )

        nested_rpc_key_prefix = _build_rpc_profiling_key(
            RPCExecMode.ASYNC, slow_add.__qualname__, dst1, dst2
        )
        expected_key = key_prefix + REMOTE_OP_STR + nested_rpc_key_prefix
        remote_events = [event for event in function_events if event.is_remote]
        rpc_remote_event = [
            event for event in remote_events if event.name == expected_key
        ]
        self.assertEqual(1, len(rpc_remote_event))
        rpc_remote_event = rpc_remote_event[0]
        self.assertEqual(rpc_remote_event.node_id, (self.rank + 1) % self.world_size)
        # slow_async_add's RPC does an add on dst2, which should be reflected as well.
        remote_add_key = (
            expected_key + REMOTE_OP_STR + torch.jit._builtins._find_builtin(torch.add)
        )
        remote_add_event = [
            event for event in remote_events if event.name == remote_add_key
        ]
        self.assertEqual(1, len(remote_add_event))
        remote_add_event = remote_add_event[0]
        # Validate that node_id is dst2.
        self.assertEqual(remote_add_event.node_id, (self.rank + 2) % self.world_size)