def test_watch_glob_uses_existing_parent_directories(self):
        with mock.patch.object(self.reloader, "_subscribe") as mocked_subscribe:
            self.reloader._watch_glob(self.tempdir / "does_not_exist", ["*"])
        self.assertSequenceEqual(
            mocked_subscribe.call_args[0],
            [
                self.tempdir,
                "glob-parent-does_not_exist:%s" % self.tempdir,
                ["anyof", ["match", "does_not_exist/*", "wholename"]],
            ],
        )