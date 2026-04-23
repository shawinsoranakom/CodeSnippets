def _test_ddp_logging_data(self, is_gpu):
            rank = dist.get_rank()
            model_DDP = Net()
            if is_gpu:
                model_DDP = nn.parallel.DistributedDataParallel(
                    model_DDP.cuda(rank), device_ids=[rank]
                )
            else:
                model_DDP = nn.parallel.DistributedDataParallel(model_DDP)

            # dummy data initialization
            local_bs = 2
            batch_size, input, target, loss = self._prepare_dummy_data(local_bs)
            if is_gpu:
                input = input.cuda(rank)
                target = target.cuda(rank)

            model_DDP._set_ddp_runtime_logging_sample_rate(2)

            for idx in range(20):
                offset = rank * local_bs

                # DDP training, DDP scatters subsets of input to nodes/GPUs
                self._test_DDP_helper(
                    model_DDP,
                    input[offset : offset + local_bs],
                    target[offset : offset + local_bs],
                    loss,
                    1,
                )

                self._model_step_with_zero_grad(model_DDP)

                # Verify DDP logging data is sampled as expected
                # If it has ran more than 10 iterations and this is
                # the sampled iteration for measuring run time stats,
                # the run time stats for this idx-th iteration will not
                # be zeros.
                ddp_logging_data = model_DDP._get_ddp_logging_data()
                if idx > 0 and (idx < 10 or idx % 2 == 0):
                    self.assertGreaterEqual(
                        ddp_logging_data.get("forward_compute_time"), 1
                    )
                    self.assertGreaterEqual(
                        ddp_logging_data.get("backward_compute_time"), 1
                    )
                    self.assertGreaterEqual(
                        ddp_logging_data.get("backward_comm_time"), 1
                    )
                    self.assertGreaterEqual(
                        ddp_logging_data.get("backward_compute_time"),
                        ddp_logging_data.get("backward_compute_comm_overlap_time"),
                    )
                    self.assertGreaterEqual(
                        ddp_logging_data.get("backward_comm_time"),
                        ddp_logging_data.get("backward_compute_comm_overlap_time"),
                    )
                    self.assertEqual(ddp_logging_data.get("iteration"), idx)
                elif idx > 0:
                    # if the idx-th iteration is not sampled to set runtime stats,
                    # ddp_logging_data.iteration will not be updated to current
                    # iteration.
                    self.assertNotEqual(ddp_logging_data.get("iteration"), idx)

                # Shuffle the input so that DDP input is different
                input = input[torch.randperm(batch_size)]

            return model_DDP