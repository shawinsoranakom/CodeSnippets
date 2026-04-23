def test_one_expressions(self):
        with self.assertRaisesMessage(
            ValueError, "Greatest must take at least two expressions"
        ):
            Greatest("written")