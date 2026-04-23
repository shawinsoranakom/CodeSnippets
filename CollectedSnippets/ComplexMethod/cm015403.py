def test_individual_send_recv(self, op_sizes, timing_enabled):
        """
        'WorkEnqueue' was skipped for isendirecv, leading to segfault on dump_entries when update_state tried to use
        a destructed Work obj's cuda events
        """

        if self.rank == self.MAIN_PROCESS_RANK:
            return
        pg = self._create_process_group_nccl()
        if timing_enabled:
            pg._enable_collectives_timing()
        num_repeats = 10
        ops_per_repeat = len(op_sizes)
        for _ in range(num_repeats):
            for input_sizes in op_sizes:
                tensor = torch.zeros(input_sizes).to(self.local_device)
                if self.rank == 0:
                    dist.recv(tensor, 1)
                elif self.rank == 1:
                    tensor *= 2
                    dist.send(tensor, 0)

        torch.cuda.synchronize(device=self.local_device)
        if timing_enabled:
            # wait for watchdog thread to process the queue of works
            time.sleep(1)

        t = pickle.loads(torch._C._distributed_c10d._dump_nccl_trace())
        self.assertEqual(len(t["entries"]), num_repeats * (ops_per_repeat))
        expected_seq = 1
        expected_op_id = 1
        for seq in range(num_repeats * ops_per_repeat):
            input_sizes = op_sizes[seq % ops_per_repeat]
            profiling_name = "nccl:recv 0<-1" if self.rank == 0 else "nccl:send 1->0"
            self.assertEqual(t["entries"][seq]["profiling_name"], profiling_name)
            # we don't increment collective_seq_id for p2p ops.
            self.assertEqual(t["entries"][seq]["collective_seq_id"], 0)
            self.assertEqual(t["entries"][seq]["p2p_seq_id"], expected_seq)
            expected_seq += 1
            self.assertEqual(t["entries"][seq]["op_id"], expected_op_id)
            expected_op_id += 1
            self.assertEqual(t["entries"][seq]["input_sizes"], [input_sizes])
            self.assertEqual(t["entries"][seq]["output_sizes"], [input_sizes])
            self.assertEqual(t["entries"][seq]["state"], "completed")

            if timing_enabled:
                duration = t["entries"][seq]["duration_ms"]
                self.assertTrue(0.001 < duration < 10000, duration)
            else:
                self.assertTrue("duration_ms" not in t["entries"][seq])