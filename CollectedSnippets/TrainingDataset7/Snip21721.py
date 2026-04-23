def test_regression_7961(self):
        """
        Regression test for #7961: When not using a portion of an
        extra(...) in a query, remove any corresponding parameters from the
        query as well.
        """
        self.assertEqual(
            list(
                User.objects.extra(select={"alpha": "%s"}, select_params=(-6,))
                .filter(id=self.u.id)
                .values_list("id", flat=True)
            ),
            [self.u.id],
        )