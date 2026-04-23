def _test_send_recv_with_tag(self, profiler_ctx):
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            send_recv_size = 10
            tensor = _build_tensor(send_recv_size, value=rank)
            ctx = profiler_ctx if profiler_ctx is not None else nullcontext()
            with ctx as prof:
                for dst in range(world_size):
                    if dst == rank:
                        # Recv mode
                        for src in range(world_size):
                            if src == rank:
                                continue
                            output_tensor = _build_tensor(send_recv_size, value=-1)
                            dist.recv(output_tensor, src, tag=src)
                            self.assertTrue(output_tensor.eq(src).all())
                    else:
                        # Send mode
                        dist.send(tensor, dst, tag=rank)

            if profiler_ctx is not None:
                backend = dist.get_backend()
                if backend in SEND_RECV_PROFILING_SUPPORTED_BACKENDS:
                    for event_name in [f"{backend}:send", f"{backend}:recv"]:
                        events = get_profiling_event(event_name, prof)
                        # Each rank sends/recvs from all other ranks
                        event_count = sum(e.count for e in events)
                        expected_event_count = dist.get_world_size() - 1
                        self.assertEqual(event_count, expected_event_count)
                        for event in events:
                            self.assertTrue(event.is_async)
                            self.assertEqual(event.name, event_name)
                            self.assertEqual(event.input_shapes, [[send_recv_size] * 3])