def test_profiler_rpc_record_shapes(self):
        if self.rank != 1:
            return
        dst = (self.rank + 1) % self.world_size
        dst_worker = worker_name(dst)
        t1, t2 = torch.ones(100), torch.ones(100)
        with _profile(record_shapes=True) as prof:
            rpc.rpc_sync(dst_worker, torch.add, args=(t1, t2))

        function_events = prof.function_events
        remote_events = [event for event in function_events if event.is_remote]
        remote_add_event = next(
            event for event in remote_events if "aten::add" in event.name
        )
        remote_add_input_shapes = remote_add_event.input_shapes
        # Run profiler on equivalent local op and validate shapes are the same.
        with _profile(record_shapes=True) as prof:
            torch.add(t1, t2)

        local_function_events = prof.function_events
        local_add_event = next(
            event for event in local_function_events if "aten::add" in event.name
        )
        local_add_input_shapes = local_add_event.input_shapes
        self.assertEqual(remote_add_input_shapes, local_add_input_shapes)