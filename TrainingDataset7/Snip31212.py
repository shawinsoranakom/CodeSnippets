def test_tell(self):
        r = HttpResponseBase()
        with self.assertRaisesMessage(
            OSError, "This HttpResponseBase instance cannot tell its position"
        ):
            r.tell()