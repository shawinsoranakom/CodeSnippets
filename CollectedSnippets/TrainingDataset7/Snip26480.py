def test_extra_tags(self):
        """
        A message's extra_tags attribute is correctly preserved when retrieved
        from the message storage.
        """
        for extra_tags in ["", None, "some tags"]:
            with self.subTest(extra_tags=extra_tags):
                self.assertEqual(
                    self.encode_decode("message", extra_tags=extra_tags).extra_tags,
                    extra_tags,
                )