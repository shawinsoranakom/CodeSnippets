def test_sum_star_exception(self):
        msg = "Star cannot be used with filter. Please specify a field."
        with self.assertRaisesMessage(ValueError, msg):
            Count("*", filter=Q(age=40))