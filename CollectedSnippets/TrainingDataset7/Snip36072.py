def test_check_availability(self, mocked_client):
        mocked_client().capabilityCheck.side_effect = Exception()
        with self.assertRaisesMessage(
            WatchmanUnavailable, "Cannot connect to the watchman service"
        ):
            self.RELOADER_CLS.check_availability()