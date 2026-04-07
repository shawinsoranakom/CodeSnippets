def test_repr(self):
        self.assertEqual(
            repr(self.reference), "<Columns 'FIRST_COLUMN, SECOND_COLUMN'>"
        )