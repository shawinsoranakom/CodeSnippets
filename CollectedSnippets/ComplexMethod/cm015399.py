def test_trace_while_active(self, timing_enabled, only_active):
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
            if self.rank != 0:
                pg.allreduce(a).wait()
            e.synchronize()
            t = pickle.loads(
                torch._C._distributed_c10d._dump_nccl_trace(onlyActive=only_active)
            )
            t = t["entries"]
            if only_active:
                if self.rank == 0:
                    self.assertEqual(len(t), 0)
                else:
                    self.assertEqual(len(t), 1)
            if not only_active:
                if self.rank == 0:
                    self.assertEqual(t[-1]["profiling_name"], "nccl:all_reduce")
                    self.assertEqual(t[-1]["collective_seq_id"], 1)
                    self.assertEqual(t[-1]["state"], "completed")
                else:
                    self.assertEqual(t[-1]["profiling_name"], "nccl:all_reduce")
                    self.assertEqual(t[-1]["collective_seq_id"], 2)

                    # ROCm runtime used to call uSleep(20 µs)inside the default‑signal busy-wait loop.
                    # Now, this sleep is removed which lets the host thread spin continuously
                    # Therefore, the state can either be scheduled or started before test dumps the trace.
                    if (
                        torch.version.hip
                        and _get_torch_rocm_version() >= (6, 4)
                        and timing_enabled
                    ):
                        if t[-1]["state"] not in ("scheduled", "started"):
                            raise AssertionError(
                                f"Expected state in ('scheduled', 'started'), got {t[-1]['state']}"
                            )
                    else:
                        self.assertEqual(
                            t[-1]["state"], self.started_or_scheduled(timing_enabled)
                        )

            self.parent.send("next")
            self.assertEqual("next", self.parent.recv())
            if self.rank == 0:
                pg.allreduce(a).wait()
            torch.cuda.synchronize(device=device)