def test_questioner_no_default_keyboard_interrupt(self, mock_input):
        with self.assertRaises(SystemExit):
            self.questioner._ask_default()
        self.assertIn("Cancelled.\n", self.prompt.getvalue())