def test_cuda_is_available(self, avoid_init, nvml_avail):
        if IS_JETSON and nvml_avail and avoid_init == "1":
            self.skipTest("Not working for Jetson")
        patch_env = {"PYTORCH_NVML_BASED_CUDA_CHECK": avoid_init} if avoid_init else {}
        with patch.dict(os.environ, **patch_env):
            if nvml_avail:
                _ = torch.cuda.is_available()
            else:
                with patch.object(torch.cuda, "_device_count_nvml", return_value=-1):
                    _ = torch.cuda.is_available()
            with multiprocessing.get_context("fork").Pool(1) as pool:
                in_bad_fork = pool.apply(TestExtendedCUDAIsAvail.in_bad_fork_test)
            if os.getenv("PYTORCH_NVML_BASED_CUDA_CHECK") == "1" and nvml_avail:
                self.assertFalse(
                    in_bad_fork, TestExtendedCUDAIsAvail.SUBPROCESS_REMINDER_MSG
                )
            else:
                if not in_bad_fork:
                    raise AssertionError("expected in_bad_fork to be True")