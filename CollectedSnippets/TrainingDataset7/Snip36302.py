def test_repercent_broken_unicode_small_fragments(self):
        data = b"test\xfctest\xfctest\xfc"
        decoded_paths = []

        def mock_quote(*args, **kwargs):
            # The second frame is the call to repercent_broken_unicode().
            decoded_paths.append(inspect.currentframe().f_back.f_locals["path"])
            return quote(*args, **kwargs)

        with mock.patch("django.utils.encoding.quote", mock_quote):
            self.assertEqual(repercent_broken_unicode(data), b"test%FCtest%FCtest%FC")

        # decode() is called on smaller fragment of the path each time.
        self.assertEqual(
            decoded_paths,
            [b"test\xfctest\xfctest\xfc", b"test\xfctest\xfc", b"test\xfc"],
        )