def test_unsupported(self):
        msg = "SHA224 is not supported on Oracle."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Author.objects.annotate(sha224_alias=SHA224("alias")).first()