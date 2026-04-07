def test_logentry_get_edited_object(self):
        """
        LogEntry.get_edited_object() returns the edited object of a LogEntry
        object.
        """
        logentry = LogEntry.objects.get(content_type__model__iexact="article")
        edited_obj = logentry.get_edited_object()
        self.assertEqual(logentry.object_id, str(edited_obj.pk))