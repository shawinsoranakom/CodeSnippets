def test_condition_must_be_q(self):
        with self.assertRaisesMessage(
            ValueError, "Index.condition must be a Q instance."
        ):
            models.Index(condition="invalid", name="long_book_idx")