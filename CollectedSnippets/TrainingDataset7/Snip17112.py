def test_extra_select_grouping_with_params(self):
        # Regression for #10290 - extra selects with parameters can be used for
        # grouping.
        qs = (
            Book.objects.annotate(mean_auth_age=Avg("authors__age"))
            .extra(select={"sheets": "(pages + %s) / %s"}, select_params=[1, 2])
            .order_by("sheets")
            .values("sheets")
        )
        self.assertQuerySetEqual(
            qs, [150, 175, 224, 264, 473, 566], lambda b: int(b["sheets"])
        )