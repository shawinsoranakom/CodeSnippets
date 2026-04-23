def test_passing_explicit_none(self):
        msg = "get_response must be provided."
        for middleware in self.middlewares:
            with self.subTest(middleware=middleware):
                with self.assertRaisesMessage(ValueError, msg):
                    middleware(None)