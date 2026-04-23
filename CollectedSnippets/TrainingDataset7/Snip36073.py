def test_check_availability_lower_version(self, mocked_client):
        mocked_client().capabilityCheck.return_value = {"version": "4.8.10"}
        with self.assertRaisesMessage(
            WatchmanUnavailable, "Watchman 4.9 or later is required."
        ):
            self.RELOADER_CLS.check_availability()