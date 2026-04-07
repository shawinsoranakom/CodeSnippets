def test_questioner_bad_user_choice(self, mock_input):
        question = "Make a choice:"
        value = self.questioner._choice_input(question, choices="abc")
        expected_msg = f"{question}\n" f" 1) a\n" f" 2) b\n" f" 3) c\n"
        self.assertIn(expected_msg, self.prompt.getvalue())
        self.assertEqual(value, 1)