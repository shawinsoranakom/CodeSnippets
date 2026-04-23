def test_tensorboard_trace_handler(self):
        use_cuda = torch.profiler.ProfilerActivity.CUDA in supported_activities()
        with _profile(use_device="cuda" if use_cuda else None, use_kineto=True):
            self.payload(use_cuda=use_cuda)

        with TemporaryDirectoryName() as dname:
            with profile(
                activities=[torch.profiler.ProfilerActivity.CPU]
                + ([torch.profiler.ProfilerActivity.CUDA] if use_cuda else []),
                schedule=torch.profiler.schedule(wait=1, warmup=1, active=2, repeat=3),
                on_trace_ready=torch.profiler.tensorboard_trace_handler(dname),
            ) as p:
                for _ in range(18):
                    self.payload(use_cuda=use_cuda)
                    p.step()

            self.assertTrue(os.path.exists(dname))
            file_num = 0
            for file_name in os.listdir(dname):
                parts = file_name.split(".")
                self.assertTrue(len(parts) > 4)
                self.assertTrue(
                    parts[-4].isdigit() and int(parts[-4]) > 0,
                    "Wrong tracing file name pattern",
                )
                if parts[-3:] == ["pt", "trace", "json"]:
                    file_num += 1
            self.assertEqual(file_num, 3)

        # test case for gzip file format
        with TemporaryDirectoryName() as dname:
            p = profile(
                activities=[torch.profiler.ProfilerActivity.CPU]
                + ([torch.profiler.ProfilerActivity.CUDA] if use_cuda else []),
                schedule=torch.profiler.schedule(wait=1, warmup=1, active=2, repeat=3),
                on_trace_ready=torch.profiler.tensorboard_trace_handler(
                    dname, use_gzip=True
                ),
            )
            p.start()
            for _ in range(18):
                self.payload(use_cuda=use_cuda)
                p.step()
            p.stop()

            self.assertTrue(os.path.exists(dname))
            file_num = 0
            for file_name in os.listdir(dname):
                parts = file_name.split(".")
                self.assertTrue(len(parts) > 4)
                self.assertTrue(
                    parts[-5].isdigit() and int(parts[-5]) > 0,
                    "Wrong tracing file name pattern",
                )
                self.assertEqual(parts[-4:], ["pt", "trace", "json", "gz"])
                file_num += 1
            self.assertEqual(file_num, 3)