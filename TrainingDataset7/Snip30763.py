def test_slicing_without_step_is_lazy(self):
        with self.assertNumQueries(0):
            self.get_ordered_articles()[0:5]