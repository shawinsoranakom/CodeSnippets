def test_nonliterals(self):
        """Variable names that aren't resolved as literals."""
        for var in ["inf", "infinity", "iNFiniTy", "nan"]:
            with self.subTest(var=var):
                self.assertIsNone(Variable(var).literal)