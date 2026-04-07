def test_questioner_default_no_user_entry(self, mock_input):
        value = self.questioner._ask_default(default="datetime.timedelta(days=1)")
        self.assertEqual(value, datetime.timedelta(days=1))