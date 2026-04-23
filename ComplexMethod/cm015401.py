def test_batched_send_recv(self, op_sizes_per_coalesce, timing_enabled):
        """
        'WorkEnqueue' was skipped for isendirecv, leading to segfault on dump_entries when update_state tried to use
        a destructed Work obj's cuda events
        """

        if self.rank == self.MAIN_PROCESS_RANK:
            return
        pg = self._create_process_group_nccl()
        if timing_enabled:
            pg._enable_collectives_timing()

        num_coalesced_ops = 20
        ops_per_coalesce = len(op_sizes_per_coalesce)
        for _ in range(num_coalesced_ops):
            ops = []
            for input_sizes in op_sizes_per_coalesce:
                tensor = torch.zeros(input_sizes).to(self.local_device)
                if self.rank == 0:
                    ops.append(dist.P2POp(dist.irecv, tensor, 1))
                elif self.rank == 1:
                    tensor *= 2
                    ops.append(dist.P2POp(dist.isend, tensor, 0))

            dist.batch_isend_irecv(ops).pop().wait()

        torch.cuda.synchronize(device=self.local_device)

        if timing_enabled:
            # wait for watchdog thread to process the queue of works
            time.sleep(1)

        t = pickle.loads(torch._C._distributed_c10d._dump_nccl_trace())
        self.assertEqual(len(t["entries"]), num_coalesced_ops * (ops_per_coalesce + 1))

        expected_record_id = 0
        expected_seq = 1
        expected_op_id = 1
        for seq in range(num_coalesced_ops):
            first_op = seq * (ops_per_coalesce + 1)
            coalesced_op = first_op + ops_per_coalesce
            for p2p_op_idx, input_sizes in zip(
                range(first_op, coalesced_op, 1), op_sizes_per_coalesce
            ):
                # the individual ops inside the coalescing group the individual op metadata,
                # but not the timing info coming from the actual coalesced kernel
                profiling_name = (
                    "nccl:recv 0<-1" if self.rank == 0 else "nccl:send 1->0"
                )
                self.assertEqual(
                    t["entries"][p2p_op_idx]["record_id"], expected_record_id
                )
                expected_record_id += 1
                self.assertEqual(
                    t["entries"][p2p_op_idx]["profiling_name"], profiling_name
                )
                # we don't increment collective_seq_id for p2p ops.
                self.assertEqual(t["entries"][p2p_op_idx]["collective_seq_id"], 0)
                self.assertEqual(t["entries"][p2p_op_idx]["p2p_seq_id"], expected_seq)
                self.assertEqual(t["entries"][p2p_op_idx]["op_id"], expected_op_id)
                expected_op_id += 1
                self.assertEqual(t["entries"][p2p_op_idx]["input_sizes"], [input_sizes])
                self.assertEqual(
                    t["entries"][p2p_op_idx]["output_sizes"], [input_sizes]
                )
                # duration doesn't get tagged onto individual ops yet, nor is their state updated
                self.assertEqual(t["entries"][p2p_op_idx]["state"], "scheduled")
                self.assertTrue("duration_ms" not in t["entries"][p2p_op_idx])

            # the coalesced op has no metadata but indicates that coalescing was used,
            # and accurately reflects the timing and state info for the whole group
            self.assertEqual(
                t["entries"][coalesced_op]["record_id"], expected_record_id
            )
            expected_record_id += 1
            self.assertEqual(
                t["entries"][coalesced_op]["profiling_name"], "nccl:coalesced"
            )
            self.assertEqual(t["entries"][coalesced_op]["p2p_seq_id"], expected_seq)
            expected_seq += 1
            self.assertEqual(t["entries"][coalesced_op]["state"], "completed")
            self.assertEqual(t["entries"][coalesced_op]["input_sizes"], [])
            self.assertEqual(t["entries"][coalesced_op]["output_sizes"], [])
            if timing_enabled:
                duration = t["entries"][coalesced_op]["duration_ms"]
                self.assertTrue(0.001 < duration < 10000, duration)
            else:
                self.assertTrue("duration_ms" not in t["entries"][coalesced_op])
            self.assertEqual(t["entries"][coalesced_op]["timeout_ms"], 600000)