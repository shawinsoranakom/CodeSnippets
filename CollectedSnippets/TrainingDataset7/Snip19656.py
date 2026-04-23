def test_field_conflicts(self):
        test_cases = (
            ({"pk": (1, 1), "id": 2}, (1, 1)),
            ({"id": 2, "pk": (1, 1)}, (1, 1)),
            ({"pk": (1, 1), "tenant_id": 2}, (1, 1)),
            ({"tenant_id": 2, "pk": (1, 1)}, (1, 1)),
            ({"pk": (2, 2), "tenant_id": 3, "id": 4}, (2, 2)),
            ({"tenant_id": 3, "id": 4, "pk": (2, 2)}, (2, 2)),
        )

        for kwargs, pk in test_cases:
            with self.subTest(kwargs=kwargs):
                user = User(**kwargs)
                self.assertEqual(user.pk, pk)