def test_logentry_unicode(self):
        log_entry = LogEntry()

        log_entry.action_flag = ADDITION
        self.assertTrue(str(log_entry).startswith("Added "))

        log_entry.action_flag = CHANGE
        self.assertTrue(str(log_entry).startswith("Changed "))

        log_entry.action_flag = DELETION
        self.assertTrue(str(log_entry).startswith("Deleted "))

        # Make sure custom action_flags works
        log_entry.action_flag = 4
        self.assertEqual(str(log_entry), "LogEntry Object")