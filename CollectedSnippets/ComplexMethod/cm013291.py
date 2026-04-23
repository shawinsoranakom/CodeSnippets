def _test_ddp_profiling(self, profiler_ctx, profiler_ctx2=None):
            """Runs DDP based model training and captures profiles.
            This test will do two profiler runs.
            1. An initial basic run to check if profiler events are correctly captured.
            2. A second profiling pass after running some iterations of DDP, to check robustness of thread local state.

            args
                profiler_ctx : Profiler context manager for pass 1
                profiler_ctx2 : Profiler context manager for pass 2.
                    This can be left out as None, in which case a deepcopy
                    of profiler_ctx is used.
            Returns:
                prof: Instantiated profiler object that can be used for post analysis.
            """
            batch = 3
            dim = 10
            num_iters = 6
            torch.cuda.set_device(self.rank)
            model = nn.Linear(dim, dim, bias=False)
            inp = torch.rand(batch, dim, device=self.rank)
            net = torch.nn.parallel.DistributedDataParallel(
                model.cuda(self.rank),
                device_ids=[self.rank],
            )
            if profiler_ctx2 is None:
                profiler_ctx2 = copy.deepcopy(profiler_ctx)

            with profiler_ctx as prof:
                for _ in range(num_iters):
                    loss = net(inp).sum()
                    loss.backward()

            all_reduce_event_name = f"{dist.get_backend()}:all_reduce"
            events = get_profiling_event(
                all_reduce_event_name, prof, dedup_gpu_user_annotation=True
            )
            event_count = sum(e.count for e in events)
            self.assertEqual(event_count, num_iters)
            for event in events:
                self.assertTrue(event.is_async)
                self.assertEqual(event.name, all_reduce_event_name)

            broadcast_event_name = f"{dist.get_backend()}:broadcast"
            broadcast_events = get_profiling_event(
                broadcast_event_name, prof, dedup_gpu_user_annotation=True
            )
            event_count = sum(e.count for e in broadcast_events)
            # Broadcast is called during rebuild_buckets
            self.assertGreaterEqual(event_count, 1)
            for event in broadcast_events:
                self.assertEqual(event.name, broadcast_event_name)

            # Run DDP with profiling for a few iterations, then enable profiling
            # for a single pass, and ensure it is recorded. This tests that the
            # thread local state is correctly updated.
            net = torch.nn.parallel.DistributedDataParallel(
                model.cuda(self.rank),
                device_ids=[self.rank],
                find_unused_parameters=True,
            )
            for _ in range(3):
                loss = net(inp).sum()
                loss.backward()
            # Now enable the profiler.
            with profiler_ctx2 as prof:
                loss = net(inp).sum()
                loss.backward()

            events = get_profiling_event(
                all_reduce_event_name, prof, dedup_gpu_user_annotation=True
            )
            self.assertGreaterEqual(len(events), 1)
            self.assertGreaterEqual(events[0].count, 1)
            self.assertEqual(events[0].name, all_reduce_event_name)
            for event in events:
                self.assertTrue(event.is_async)
            # Ensure searching unused parameters was profiled
            events = get_profiling_event("search_unused_parameters", prof)
            self.assertEqual(len(events), 1)

            return prof