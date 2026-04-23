def test_logentry_change_message_not_json(self):
        """LogEntry.change_message was a string before Django 1.10."""
        logentry = LogEntry(change_message="non-JSON string")
        self.assertEqual(logentry.get_change_message(), logentry.change_message)