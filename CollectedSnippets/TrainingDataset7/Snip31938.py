def test_cache_set_failure_non_fatal(self):
        """Failing to write to the cache does not raise errors."""
        session = self.backend()
        session["key"] = "val"

        with self.assertLogs("django.contrib.sessions", "ERROR") as cm:
            session.save()

        # A proper ERROR log message was recorded.
        log = cm.records[-1]
        self.assertEqual(log.message, f"Error saving to cache ({session._cache})")
        self.assertEqual(str(log.exc_info[1]), "Faked exception saving to cache")