def test_prep_address_without_force_ascii(self):
        # A subclass implementing SMTPUTF8 could use
        # prep_address(force_ascii=False).
        backend = smtp.EmailBackend()
        for case in ["åh@example.dk", "oh@åh.example.dk", "åh@åh.example.dk"]:
            with self.subTest(case=case):
                self.assertEqual(backend.prep_address(case, force_ascii=False), case)