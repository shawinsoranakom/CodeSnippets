def test_kineto(self):
        use_cuda = torch.profiler.ProfilerActivity.CUDA in supported_activities()
        use_device = "cuda" if use_cuda else None
        with _profile(use_device=use_device, use_kineto=True):
            self.payload(use_cuda=use_cuda)

        # rerun to avoid initial start overhead
        with _profile(use_device=use_device, use_kineto=True) as p:
            self.payload(use_cuda=use_cuda)

        self.assertTrue("aten::mm" in str(p))

        output = p.key_averages().table(
            sort_by="self_cuda_time_total" if use_cuda else "self_cpu_time_total",
            row_limit=-1,
        )
        # print(output)
        found_gemm = False
        found_memcpy = False
        found_mm = False
        for e in p.function_events:
            if "aten::mm" in e.name:
                found_mm = True
            if "gemm" in e.name.lower() or "Cijk" in e.name:
                found_gemm = True
            if "memcpy" in e.name.lower() or "__amd_rocclr_copyBuffer" in e.name:
                found_memcpy = True
        if use_cuda:
            self.assertTrue(found_gemm)
            self.assertTrue(found_memcpy)
        else:
            self.assertTrue(found_mm)
        self._check_stats(p._stats)