def test_questioner_no_default_no_user_entry_boolean(self, mock_input):
        value = self.questioner._boolean_input("Proceed?")
        self.assertIs(value, False)