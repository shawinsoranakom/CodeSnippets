def test_debug_info(self):
        initialize_pg(self.file_init_method, self.rank, self.world_size)

        t1 = torch.rand((3, 3), requires_grad=True)
        t2 = torch.rand((3, 3), requires_grad=True)
        with dist_autograd.context() as context_id:
            i = 0
            res = {}
            res[i] = t1
            for rank in range(self.world_size):
                if rank != self.rank:
                    res[i + 1] = rpc.rpc_sync(
                        worker_name(rank), torch.add, args=(res[i], t2)
                    )
                    i += 1

            # Call custom function in middle of backward pass to ensure all
            # nodes are still waiting on a backward().
            res[i + 1] = DistAutogradTest.TestDebugInfoFunc.apply(res[i])
            i += 1

            for rank in range(self.world_size):
                if rank != self.rank:
                    res[i + 1] = rpc.rpc_sync(
                        worker_name(rank), torch.add, args=(res[i], t2)
                    )
                    i += 1

            dist_autograd.backward(context_id, [res[i].sum()])

            debug_info = dist_autograd._get_debug_info()
            num_autograd_context = int(debug_info["num_autograd_contexts"])
            # Need at least one context and not more than 4.
            self.assertTrue(num_autograd_context >= 1 and num_autograd_context <= 4)

        for rd in range(self.world_size - 1):
            rpc.rpc_sync(
                worker_name((self.rank + rd + 1) % self.world_size),
                _set_rpc_done,
                args=(context_id, rd + 1),
            )

        dist.barrier()

        # Validate information
        debug_info = dist_autograd._get_debug_info()
        if debug_info is None:
            raise AssertionError("Expected debug_info to not be None")
        self.assertEqual(0, int(debug_info["num_current_backward_passes"]))
        # only have `num_current_backward_passes` and `num_autograd contexts`
        self.assertTrue(len(debug_info) == 2)

        self.assertTrue(_all_contexts_cleaned_up())

        # All contexts should be cleaned up.
        debug_info = dist_autograd._get_debug_info()
        self.assertEqual(0, int(debug_info["num_autograd_contexts"]))