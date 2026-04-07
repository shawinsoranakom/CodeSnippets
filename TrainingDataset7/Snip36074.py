def test_pywatchman_not_available(self):
        with mock.patch.object(autoreload, "pywatchman") as mocked:
            mocked.__bool__.return_value = False
            with self.assertRaisesMessage(
                WatchmanUnavailable, "pywatchman not installed."
            ):
                self.RELOADER_CLS.check_availability()