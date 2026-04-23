def test_profiler_remote_cuda(self):
        if self.rank != 1:
            return

        dst_cuda_0 = (self.rank + 1) % self.world_size
        dst_cuda_1 = (self.rank + 2) % self.world_size
        dst_worker_cuda_0 = worker_name(dst_cuda_0)
        dst_worker_cuda_1 = worker_name(dst_cuda_1)

        with _profile(use_cuda=True) as p:
            fut1 = rpc.rpc_async(dst_worker_cuda_0, udf_with_torch_ops, args=(0,))
            fut2 = rpc.rpc_async(dst_worker_cuda_1, udf_with_torch_ops, args=(1,))
            fut1.wait()
            fut2.wait()

        def get_name(event):
            return event.name[event.name.find(REMOTE_OP_STR) + len(REMOTE_OP_STR) :]

        function_events = p.function_events
        for event in function_events:
            if event.is_async:
                self.assertEqual(0, event.device_time_total)
                self.assertEqual([], event.kernels)
                self.assertEqual(0, event.device_time)
            else:
                if event.node_id == 1:
                    continue
                self.assertTrue(event.node_id in [dst_cuda_0, dst_cuda_1])
                if get_name(event) in EXPECTED_REMOTE_EVENTS:
                    self.assertGreater(event.device_time_total, 0)
                    self.assertEqual(1, len(event.kernels))
                    kernel = event.kernels[0]
                    if event.node_id == dst_cuda_0:
                        self.assertEqual(kernel.device, 0)
                    if event.node_id == dst_cuda_1:
                        self.assertEqual(kernel.device, 1)
                    self.assertGreater(event.device_time, 0)

        # Validate that EXPECTED_REMOTE_EVENTS is a subset of remotely profiled
        # events.
        remote_events = [event for event in function_events if event.is_remote]
        remote_event_names = [
            get_name(event)
            for event in remote_events
            if get_name(event) in EXPECTED_REMOTE_EVENTS
        ]
        self.assertEqual(set(remote_event_names), set(EXPECTED_REMOTE_EVENTS))