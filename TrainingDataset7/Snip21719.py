def test_extra_stay_tied(self):
        # Extra select parameters should stay tied to their corresponding
        # select portions. Applies when portions are updated or otherwise
        # moved around.
        qs = User.objects.extra(
            select={"alpha": "%s", "beta": "2", "gamma": "%s"}, select_params=(1, 3)
        )
        qs = qs.extra(select={"beta": 4})
        qs = qs.extra(select={"alpha": "%s"}, select_params=[5])
        self.assertEqual(
            list(qs.filter(id=self.u.id).values("alpha", "beta", "gamma")),
            [{"alpha": 5, "beta": 4, "gamma": 3}],
        )