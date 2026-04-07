def test_is_pk_unset(self):
        cases = [
            Article(),
            Article(id=None),
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertIs(case._is_pk_set(), False)