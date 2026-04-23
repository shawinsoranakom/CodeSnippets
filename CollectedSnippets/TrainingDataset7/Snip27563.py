def test_questioner_no_choice_keyboard_interrupt(self, mock_input):
        question = "Make a choice:"
        with self.assertRaises(SystemExit):
            self.questioner._choice_input(question, choices="abc")
        expected_msg = (
            f"{question}\n"
            f" 1) a\n"
            f" 2) b\n"
            f" 3) c\n"
            f"Select an option: \n"
            f"Cancelled.\n"
        )
        self.assertIn(expected_msg, self.prompt.getvalue())