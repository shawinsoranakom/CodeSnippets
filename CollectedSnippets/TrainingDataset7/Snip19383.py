def test_with_security_middleware(self):
        self.assertEqual(base.check_security_middleware(None), [])