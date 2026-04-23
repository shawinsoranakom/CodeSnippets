def test_invalid_target_id(self):
        for test_str in ("Iñtërnâtiônàlizætiøn", "1234'", -1234):
            # This should result in an error message, not a server exception.
            response = self.client.post(
                reverse("admin:admin_widgets_event_add"), {"main_band": test_str}
            )

            self.assertContains(
                response,
                "Select a valid choice. That choice is not one of the available "
                "choices.",
            )