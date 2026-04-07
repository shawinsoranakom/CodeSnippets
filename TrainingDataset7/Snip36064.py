def test_watch_glob_ignores_non_existing_directories_two_levels(self):
        with mock.patch.object(self.reloader, "_subscribe") as mocked_subscribe:
            self.reloader._watch_glob(self.tempdir / "does_not_exist" / "more", ["*"])
        self.assertFalse(mocked_subscribe.called)