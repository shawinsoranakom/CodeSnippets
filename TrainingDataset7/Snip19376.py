def test_with_csrf_middleware(self):
        self.assertEqual(csrf.check_csrf_middleware(None), [])