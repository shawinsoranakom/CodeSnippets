def test_regression_7957(self):
        """
        Regression test for #7957: Combining extra() calls should leave the
        corresponding parameters associated with the right extra() bit. I.e.
        internal dictionary must remain sorted.
        """
        self.assertEqual(
            (
                User.objects.extra(select={"alpha": "%s"}, select_params=(1,))
                .extra(select={"beta": "%s"}, select_params=(2,))[0]
                .alpha
            ),
            1,
        )

        self.assertEqual(
            (
                User.objects.extra(select={"beta": "%s"}, select_params=(1,))
                .extra(select={"alpha": "%s"}, select_params=(2,))[0]
                .alpha
            ),
            2,
        )