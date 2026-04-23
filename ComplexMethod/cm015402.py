def test_batched_send_recv_compiled(self, op_sizes_per_coalesce, timing_enabled):
        def _pattern(tensors):
            ops = list()
            for tensor in tensors:
                if self.rank == 0:
                    ops.append(dist.P2POp(dist.irecv, tensor, 1))
                elif self.rank == 1:
                    ops.append(dist.P2POp(dist.isend, tensor, 0))
                else:
                    raise NotImplementedError
            for work in dist.batch_isend_irecv(ops):
                work.wait()

        if self.rank == self.MAIN_PROCESS_RANK:
            return
        pg = self._create_process_group_nccl()
        if timing_enabled:
            pg._enable_collectives_timing()

        compiled_fn = torch.compile(_pattern)

        num_coalesced_ops = 20
        ops_per_coalesce = len(op_sizes_per_coalesce)

        for _ in range(num_coalesced_ops):
            if self.rank == 0:
                tensors = [
                    torch.zeros(input_sizes).to(self.local_device)
                    for input_sizes in op_sizes_per_coalesce
                ]
            elif self.rank == 1:
                tensors = [
                    torch.full(input_sizes, 2.0).to(self.local_device)
                    for input_sizes in op_sizes_per_coalesce
                ]
            else:
                raise NotImplementedError

            compiled_fn(tensors)
            if self.rank == 0:
                self.assertEqual(len(tensors), ops_per_coalesce)
                for tensor, input_sizes in zip(tensors, op_sizes_per_coalesce):
                    self.assertEqual(
                        tensor, torch.full(input_sizes, 2.0, device=self.local_device)
                    )

        torch.cuda.synchronize()

        if timing_enabled:
            time.sleep(1)

        t = pickle.loads(torch._C._distributed_c10d._dump_nccl_trace())
        self.assertTrue(len(t["entries"]) > 0)
        expected_total_entries = num_coalesced_ops * (ops_per_coalesce + 1)
        self.assertEqual(len(t["entries"]), expected_total_entries)

        for seq in range(num_coalesced_ops):
            coalesced_op_idx = seq * (ops_per_coalesce + 1) + ops_per_coalesce

            self.assertEqual(
                t["entries"][coalesced_op_idx]["profiling_name"], "nccl:coalesced"
            )
            try:
                self.assertEqual(t["entries"][coalesced_op_idx]["state"], "completed")
            except Exception:
                self.assertEqual(t["entries"][coalesced_op_idx]["state"], "scheduled")