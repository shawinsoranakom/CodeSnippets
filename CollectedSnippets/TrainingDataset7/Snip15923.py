def test_logentry_save(self):
        """
        LogEntry.action_time is a timestamp of the date when the entry was
        created. It shouldn't be updated on a subsequent save().
        """
        logentry = LogEntry.objects.get(content_type__model__iexact="article")
        action_time = logentry.action_time
        logentry.save()
        self.assertEqual(logentry.action_time, action_time)