def test_questioner_default_no_user_entry_boolean(self, mock_input):
        value = self.questioner._boolean_input("Proceed?", default=True)
        self.assertIs(value, True)