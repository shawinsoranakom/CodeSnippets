def _test_send_recv(self, profiler_ctx):
            rank = dist.get_rank()
            send_size = rank + 1
            tensor = _build_tensor(send_size)
            ctx = profiler_ctx if profiler_ctx is not None else nullcontext()
            with ctx as prof:
                for src in range(dist.get_world_size()):
                    if src == rank:
                        # Send mode
                        for dst in range(dist.get_world_size()):
                            if dst == rank:
                                continue
                            dist.send(tensor, dst)
                    else:
                        # Recv mode
                        recv_size = src + 1
                        expected_tensor = _build_tensor(recv_size)
                        output_tensor = _build_tensor(recv_size, value=-1)
                        dist.recv(output_tensor, src)
                        self.assertEqual(output_tensor, expected_tensor)

            if profiler_ctx is not None:
                backend = dist.get_backend()
                if backend in SEND_RECV_PROFILING_SUPPORTED_BACKENDS:
                    for event_name in [f"{backend}:send", f"{backend}:recv"]:
                        events = get_profiling_event(event_name, prof)
                        # Each rank sends/recvs from all other ranks.
                        event_count = sum(e.count for e in events)
                        expected_event_count = dist.get_world_size() - 1
                        self.assertEqual(event_count, expected_event_count)
                        # Event order is not deterministic, so simply assert their shape
                        # is found in the following list.
                        expected_shapes = [
                            [[rank + 1] * 3] for rank in range(dist.get_world_size())
                        ]
                        for event in events:
                            self.assertTrue(event.is_async)
                            self.assertTrue(event.input_shapes in expected_shapes)