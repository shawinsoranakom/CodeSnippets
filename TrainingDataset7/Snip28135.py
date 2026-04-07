def test_EmailField(self):
        lazy_func = lazy(lambda: "mailbox@domain.com", str)
        self.assertIsInstance(EmailField().get_prep_value(lazy_func()), str)