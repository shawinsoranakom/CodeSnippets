def assertChoicesDisplay(self, choices, expected_displays):
        for choice, expected_display in zip(choices, expected_displays, strict=True):
            self.assertEqual(choice["display"], expected_display)