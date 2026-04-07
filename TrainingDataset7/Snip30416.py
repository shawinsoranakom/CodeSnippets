def test_unknown_options(self):
        with self.assertRaisesMessage(ValueError, "Unknown options: TEST, TEST2"):
            Tag.objects.explain(**{"TEST": 1, "TEST2": 1})