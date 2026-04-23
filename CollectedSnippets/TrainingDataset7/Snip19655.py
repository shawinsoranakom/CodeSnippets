def test_full_clean_update(self):
        with self.assertNumQueries(1):
            self.comment_1.full_clean()