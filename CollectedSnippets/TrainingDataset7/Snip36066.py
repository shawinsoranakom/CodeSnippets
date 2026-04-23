def test_watch_glob_multiple_patterns(self):
        with mock.patch.object(self.reloader, "_subscribe") as mocked_subscribe:
            self.reloader._watch_glob(self.tempdir, ["*", "*.py"])
        self.assertSequenceEqual(
            mocked_subscribe.call_args[0],
            [
                self.tempdir,
                "glob:%s" % self.tempdir,
                ["anyof", ["match", "*", "wholename"], ["match", "*.py", "wholename"]],
            ],
        )