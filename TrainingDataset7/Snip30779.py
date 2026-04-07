def test_zero_length_values_slicing(self):
        n = 42
        with self.assertNumQueries(0):
            self.assertQuerySetEqual(Article.objects.values()[n:n], [])
            self.assertQuerySetEqual(Article.objects.values_list()[n:n], [])