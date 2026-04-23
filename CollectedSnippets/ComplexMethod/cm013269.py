def _test_send_recv_nccl(self, profiler_ctx=None):
            # TODO: now that nccl send/recv is supported, there does not seem to
            # be a need to have nccl send/recv be tested separately.
            rank = dist.get_rank()
            world_size = dist.get_world_size()
            rank_to_GPU = init_multigpu_helper(world_size, BACKEND)
            device_id = rank_to_GPU[rank][0]
            torch.cuda.set_device(device_id)

            tensor = _build_tensor(rank + 1, device_id=device_id)
            profiler_cls = profiler_ctx if profiler_ctx is not None else nullcontext()
            with profiler_cls as prof:
                for src in range(world_size):
                    if src == rank:
                        # Send mode
                        for dst in range(world_size):
                            if dst == rank:
                                continue
                            dist.send(tensor, dst)
                    else:
                        # Recv mode
                        expected_tensor = _build_tensor(src + 1)
                        output_tensor = _build_tensor(
                            src + 1, value=-1, device_id=device_id
                        )
                        dist.recv(output_tensor, src)
                        self.assertEqual(output_tensor, expected_tensor)

                self._barrier()

            if profiler_ctx is not None:
                backend = dist.get_backend()
                if backend in SEND_RECV_PROFILING_SUPPORTED_BACKENDS:
                    for event_name in [f"{backend}:send", f"{backend}:recv"]:
                        events = get_profiling_event(
                            event_name, prof, dedup_gpu_user_annotation=True
                        )
                        self.assertTrue(events)
                        # Event order is not deterministic, so simply assert their shape
                        # is found in the following list.
                        expected_shapes = [
                            [[rank + 1] * 3] for rank in range(dist.get_world_size())
                        ]
                        for event in events:
                            self.assertTrue(event.input_shapes in expected_shapes)