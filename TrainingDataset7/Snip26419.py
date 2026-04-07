def test_set_clear_non_bulk(self):
        # 2 queries for clear(), 1 for add(), and 1 to select objects.
        with self.assertNumQueries(4):
            self.r.article_set.set([self.a], bulk=False, clear=True)