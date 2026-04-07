def test_one_expressions(self):
        with self.assertRaisesMessage(
            ValueError, "Least must take at least two expressions"
        ):
            Least("written")