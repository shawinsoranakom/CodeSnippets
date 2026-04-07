def test_textchoices_empty_label(self):
        self.assertEqual(Gender.choices[0], (None, "(Undeclared)"))
        self.assertEqual(Gender.labels[0], "(Undeclared)")
        self.assertIsNone(Gender.values[0])
        self.assertEqual(Gender.names[0], "__empty__")