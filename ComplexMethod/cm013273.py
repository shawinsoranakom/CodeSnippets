def _test_isend(self, profiler_ctx):
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            ctx = profiler_ctx if profiler_ctx is not None else nullcontext()
            with ctx as prof:
                if rank == 0:
                    requests = [
                        dist.isend(_build_tensor(dest, 10), dest)
                        for dest in range(1, world_size)
                    ]
                    for request in requests:
                        request.wait()
                        self.assertTrue(request.is_completed())
                else:
                    tensor = _build_tensor(rank, -1)
                    dist.recv(tensor, 0)
                    self.assertEqual(tensor, _build_tensor(rank, 10))

                self._barrier()

            if profiler_ctx is not None:
                backend = dist.get_backend()
                if backend in SEND_RECV_PROFILING_SUPPORTED_BACKENDS:
                    expected_event_name = (
                        f"{backend}:send" if rank == 0 else f"{backend}:recv"
                    )
                    events = get_profiling_event(expected_event_name, prof)
                    event_count = sum(e.count for e in events)
                    expected_count = dist.get_world_size() - 1 if rank == 0 else 1
                    self.assertEqual(expected_count, event_count)
                    # Event ordering is not guaranteed, so simply ensure the shapes are
                    # found in the following map.
                    expected_shapes = {
                        r: [[r] * 3] for r in range(1, dist.get_world_size())
                    }
                    for event in events:
                        self.assertTrue(event.is_async)
                        self.assertEqual(event.name, expected_event_name)
                        if rank == 0:
                            self.assertTrue(
                                event.input_shapes in expected_shapes.values()
                            )
                        else:
                            self.assertEqual(event.input_shapes, expected_shapes[rank])