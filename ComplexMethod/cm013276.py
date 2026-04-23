def call_dist_op(
            self,
            profiling_title_postfix,
            is_async,
            op,
            *args,
            expect_event=True,
            secondary_op_call=None,
            profile_cuda=False,
            tensor_shapes=None,
            **kwargs,
        ):
            op_calls = [lambda: op(*args, **kwargs)]
            if secondary_op_call is not None:
                op_calls.append(secondary_op_call)

            autograd_profiler_ctx = torch.autograd.profiler.profile(
                use_cuda=profile_cuda, record_shapes=True
            )

            # TODO: move this test to use torch.profiler once kineto issues are
            # fixed internally.
            with autograd_profiler_ctx:
                works = [op_call() for op_call in op_calls]
                if is_async:
                    for work in works:
                        work.wait()

            if expect_event and dist.get_backend() in PROFILING_SUPPORTED_BACKENDS:
                # We are only interested in the backend's implementation not the dispatcher wrapper.
                events = get_profiling_event(
                    dist.get_backend() + profiling_title_postfix, autograd_profiler_ctx
                )
                # DETAIL debug mode can use a pg wrapper that issues more collectives
                # under the hood
                if dist.get_debug_level() != dist.DebugLevel.DETAIL:
                    self.assertEqual(len(events), len(op_calls))
                for e in events:
                    self.assertTrue(e.is_async)
                    self.assertEqual(e.count, 1)
                    self.assertGreaterEqual(e.cpu_time, 0)
                    # Verify tensor shapes if given
                    # DETAIL debug mode can use a pg wrapper that issues more collectives
                    # under the hood
                    if (
                        tensor_shapes is not None
                        and dist.get_debug_level() != dist.DebugLevel.DETAIL
                    ):
                        self.assertEqual(
                            e.input_shapes,
                            tensor_shapes,
                            f"event shape: {e.input_shapes} vs tensor {tensor_shapes}",
                        )