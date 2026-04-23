def patch_autoreload(self, argv):
        patch_call = mock.patch(
            "django.utils.autoreload.subprocess.run",
            return_value=CompletedProcess(argv, 0),
        )
        patches = [
            mock.patch("django.utils.autoreload.sys.argv", argv),
            mock.patch("django.utils.autoreload.sys.executable", self.executable),
            mock.patch("django.utils.autoreload.sys.warnoptions", ["all"]),
            mock.patch("django.utils.autoreload.sys._xoptions", {}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        mock_call = patch_call.start()
        self.addCleanup(patch_call.stop)
        return mock_call