def test_regression_8039(self):
        """
        Regression test for #8039: Ordering sometimes removed relevant tables
        from extra(). This test is the critical case: ordering uses a table,
        but then removes the reference because of an optimization. The table
        should still be present because of the extra() call.
        """
        self.assertQuerySetEqual(
            (
                Order.objects.extra(
                    where=["username=%s"], params=["fred"], tables=["auth_user"]
                ).order_by("created_by")
            ),
            [],
        )