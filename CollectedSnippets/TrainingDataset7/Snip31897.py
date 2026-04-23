def test_invalid_key(self):
        # Submitting an invalid session key (either by guessing, or if the db
        # has removed the key) results in a new key being generated.
        try:
            session = self.backend("1")
            session.save()
            self.assertNotEqual(session.session_key, "1")
            self.assertIsNone(session.get("cat"))
            session.delete()
        finally:
            # Some backends leave a stale cache entry for the invalid
            # session key; make sure that entry is manually deleted
            session.delete("1")