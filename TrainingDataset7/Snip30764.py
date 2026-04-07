def test_slicing_with_tests_is_not_lazy(self):
        with self.assertNumQueries(1):
            self.get_ordered_articles()[0:5:3]