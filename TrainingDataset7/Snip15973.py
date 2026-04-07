def test_build_q_object_from_lookup_parameters(self):
        parameters = {
            "title__in": [["Article 1", "Article 2"]],
            "hist__iexact": ["history"],
            "site__pk": [1, 2],
        }
        q_obj = build_q_object_from_lookup_parameters(parameters)
        self.assertEqual(
            q_obj,
            models.Q(title__in=["Article 1", "Article 2"])
            & models.Q(hist__iexact="history")
            & (models.Q(site__pk=1) | models.Q(site__pk=2)),
        )