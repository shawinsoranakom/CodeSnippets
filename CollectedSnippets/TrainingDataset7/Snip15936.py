def test_action_flag_choices(self):
        tests = ((1, "Addition"), (2, "Change"), (3, "Deletion"))
        for action_flag, display_name in tests:
            with self.subTest(action_flag=action_flag):
                log = LogEntry(action_flag=action_flag)
                self.assertEqual(log.get_action_flag_display(), display_name)