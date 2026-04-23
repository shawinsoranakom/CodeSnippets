def test_kineto_multigpu(self):
        with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
            for gpu_id in [0, 1]:
                x = torch.randn(10, 10).cuda(gpu_id)
                y = torch.randn(10, 10).cuda(gpu_id)
                z = x.matmul(y)
                torch.cuda.synchronize(gpu_id)

        is_rocm = torch.version.hip is not None
        # on ROCm, Gemm shader is hipblaslt Shader, so we use UserArgs_MT to match.
        gemm_string = "userargs_mt" if is_rocm else "gemm"
        device_string = "hip" if is_rocm else "cuda"

        device_indices = set()
        found_cuda = False
        for evt in prof.events():
            if gemm_string in evt.name.lower() and evt.device_type == DeviceType.CUDA:
                device_indices.add(evt.device_index)
            if device_string in evt.name.lower() and evt.device_type == DeviceType.CPU:
                found_cuda = True

        if is_rocm:
            # Note: On ROCm, device_indices (Node IDs) may start from values other than 0 (e.g. {2, 3})
            # because systems can contain additional (non-GPU) devices detected by the kernel,
            # resulting in offset indexing. Therefore, we validate the count of unique devices,
            # not their specific indices.
            self.assertEqual(len(device_indices), 2)
        else:
            # CUDA correctly reports logical device indices
            self.assertEqual(device_indices, {0, 1})

        self.assertTrue(found_cuda)
        self._check_stats(prof._stats())