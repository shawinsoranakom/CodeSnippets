def _run_uneven_inputs_test(
            self,
            test_case,
            iteration_mapping,
            find_unused_params,
        ):
            model = test_case.model
            inp = test_case.inp
            rank = self.rank
            sync_interval = test_case.sync_interval
            torch.cuda.set_device(rank)
            # Ensure all outstanding GPU work is completed so this test runs independently.
            dist.barrier()
            # Bucket_cap_mb is intentionally low to test allreduce scheduling when
            # there are many buckets.
            net = torch.nn.parallel.DistributedDataParallel(
                model.cuda(rank),
                device_ids=[rank],
                bucket_cap_mb=1,
                find_unused_parameters=find_unused_params,
            )
            # Register hook if specified
            if test_case.hook is not None:
                net.register_comm_hook(test_case.state, test_case.hook)
                print(f"registered hook {test_case.hook}")

            # Determine num iters for this rank via the passed in mapping.
            num_iters = iteration_mapping[rank]
            # If we throw when earliest rank terminates, we should ensure
            # that we iterate for that minimum number of times.
            num_iters_tensor = torch.tensor(
                [num_iters], device=torch.cuda.current_device()
            )
            dist.all_reduce(num_iters_tensor, op=dist.ReduceOp.MIN)
            min_num_iters = num_iters_tensor.item()
            total_iters = 0
            if test_case.throw_on_early_termination:
                if min_num_iters == num_iters:
                    # Early termination rank(s)
                    exception_ctx = self.assertRaisesRegex(
                        RuntimeError, f"Rank {self.rank} exhausted all inputs"
                    )
                else:
                    # Non early termination rank
                    exception_ctx = self.assertRaisesRegex(
                        RuntimeError,
                        "Detected at least one rank that exhausted inputs.",
                    )
            else:
                exception_ctx = nullcontext()
            with exception_ctx:
                with net.join(
                    throw_on_early_termination=test_case.throw_on_early_termination
                ):
                    for i in range(num_iters):
                        # Use model.no_sync() to disable grad synchronization every
                        # sync_interval.
                        if i % sync_interval != 0:
                            context = net.no_sync()
                        else:
                            context = nullcontext()
                        with context:
                            if isinstance(inp, tuple):
                                loss = net(*inp).sum()
                            else:
                                loss = net(inp).sum()
                            loss.backward()
                            self._model_step(net)
                            # Ensure completion of GPU kernels (including allreduce). If the
                            # join API is not properly implemented, then this should hang
                            # since the allreduce will hang.
                            torch.cuda.synchronize(device=rank)
                        total_iters += 1
            if test_case.throw_on_early_termination:
                # Ensure we iterated min_num_iters times.
                self.assertEqual(total_iters, min_num_iters)
            else:
                # Ensure we iterated at least min_num_iters times.
                self.assertGreaterEqual(total_iters, min_num_iters)

            # Ensure completion of all GPU kernels.
            torch.cuda.synchronize(device=rank)
            # When throwing on early rank termination, we do not
            # broadcast model state from an authoritative rank. All models
            # should already be in sync.
            if not test_case.throw_on_early_termination:
                self.assertTrue(net._authoritative_rank)
                # All ranks should have agreed on the same authoritative_rank!
                final_rank_tensor = torch.tensor(
                    [net._authoritative_rank], device=self.rank
                )
                tensor_list = [
                    torch.zeros_like(final_rank_tensor)
                    for _ in range(dist.get_world_size())
                ]
                dist.all_gather(tensor_list, final_rank_tensor)
                max_rank = dist.get_world_size() - 1
                self.assertSetEqual(
                    {max_rank}, {tensor.item() for tensor in tensor_list}
                )
                # Ensure that all models are the same across ranks after all have joined.
                self.validate_net_equivalence(net)
                # Ensure that running with DDP uneven inputs was logged.
                ddp_logging_data = net._get_ddp_logging_data()
                self.assertTrue(ddp_logging_data.get("join_uneven_inputs"))
                dist.barrier()