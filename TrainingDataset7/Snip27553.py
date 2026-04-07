def test_questioner_default_timedelta(self, mock_input):
        value = self.questioner._ask_default()
        self.assertEqual(value, datetime.timedelta(days=1))