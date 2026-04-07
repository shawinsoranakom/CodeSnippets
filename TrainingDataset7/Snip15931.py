def test_logentry_repr(self):
        logentry = LogEntry.objects.first()
        self.assertEqual(repr(logentry), str(logentry.action_time))