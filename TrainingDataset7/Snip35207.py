def test_assert_num_queries(self):
        def test_func():
            raise ValueError

        with self.assertRaises(ValueError):
            self.assertNumQueries(2, test_func)