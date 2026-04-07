def test_input_not_found(self):
        with self.assertRaisesMessage(
            ValueError, "Mock input for 'Email address: ' not found."
        ):
            call_command("createsuperuser", stdin=MockTTY())