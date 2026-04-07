def test_incorrect_timezone(self):
        with self.assertRaisesMessage(ValueError, "Incorrect timezone setting: test"):
            settings._setup()