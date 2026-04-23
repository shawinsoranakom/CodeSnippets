def test_trace_while_stuck(self, timing_enabled):
        if self.rank == self.MAIN_PROCESS_RANK:
            for c in self.children_pipes:
                self.assertEqual(c.recv(), "next")
            for c in self.children_pipes:
                c.send("next")
            return

        pg = self._create_process_group_nccl()
        if timing_enabled:
            pg._enable_collectives_timing()

        device = self.local_device
        with torch.cuda.device(device):
            a = torch.full((3, 4), float(self.rank), device=device)

            pg.allreduce(a).wait()
            e = torch.cuda.Event()
            e.record()

            def gather_trace():
                e.synchronize()
                # give the other thread some time to fill the cuda buffer
                time.sleep(5)
                t = pickle.loads(torch._C._distributed_c10d._dump_nccl_trace())
                t = t["entries"]
                self.assertEqual(t[-1]["profiling_name"], "nccl:all_reduce")
                if self.rank == 0:
                    self.assertEqual(t[-1]["collective_seq_id"], 1)
                    self.assertEqual(t[-1]["state"], "completed")
                else:
                    self.assertEqual(t[-1]["collective_seq_id"], 2)
                    self.assertEqual(
                        t[-1]["state"], self.started_or_scheduled(timing_enabled)
                    )
                    self.assertIsNone(t[-1]["time_discovered_completed_ns"])
                # this will eventually cause the missing rank 0
                # to continue which will unblock the non-zero ranks
                self.parent.send("next")

            if self.rank != 0:
                pg.allreduce(a).wait()
                th = threading.Thread(target=gather_trace)
                th.start()
                # fill the cuda buffer, at around 1024 events
                # this will stall
                for _ in range(2000):
                    a = a + a
                th.join()
            else:
                gather_trace()

            self.assertEqual("next", self.parent.recv())
            if self.rank == 0:
                pg.allreduce(a).wait()
            torch.cuda.synchronize(device=device)