def test_regression_8819(self):
        """
        Regression test for #8819: Fields in the extra(select=...) list
        should be available to extra(order_by=...).
        """
        self.assertSequenceEqual(
            User.objects.filter(pk=self.u.id)
            .extra(select={"extra_field": 1})
            .distinct(),
            [self.u],
        )
        self.assertSequenceEqual(
            User.objects.filter(pk=self.u.id).extra(
                select={"extra_field": 1}, order_by=["extra_field"]
            ),
            [self.u],
        )
        self.assertSequenceEqual(
            User.objects.filter(pk=self.u.id)
            .extra(select={"extra_field": 1}, order_by=["extra_field"])
            .distinct(),
            [self.u],
        )