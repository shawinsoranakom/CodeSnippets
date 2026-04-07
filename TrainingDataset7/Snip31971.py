def test_unpickling_exception(self):
        # signed_cookies backend should handle unpickle exceptions gracefully
        # by creating a new session
        self.assertEqual(self.session.serializer, JSONSerializer)
        self.session.save()
        with mock.patch("django.core.signing.loads", side_effect=ValueError):
            self.session.load()