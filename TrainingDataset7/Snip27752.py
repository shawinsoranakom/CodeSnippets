def test_textchoices_auto_label(self):
        self.assertEqual(Gender.MALE.label, "Male")
        self.assertEqual(Gender.FEMALE.label, "Female")
        self.assertEqual(Gender.NOT_SPECIFIED.label, "Not Specified")