def test_condition_requires_index_name(self):
        with self.assertRaisesMessage(
            ValueError, "An index must be named to use condition."
        ):
            models.Index(condition=models.Q(pages__gt=400))