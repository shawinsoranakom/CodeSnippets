def test_full_clean_success(self):
        test_cases = (
            # 1, 1234, {}
            ({"tenant": self.tenant_1, "id": 1234}, {}),
            ({"tenant_id": self.tenant_1.id, "id": 1234}, {}),
            ({"pk": (self.tenant_1.id, 1234)}, {}),
            # 1, 1, {"id"}
            ({"tenant": self.tenant_1, "id": 1}, {"id"}),
            ({"tenant_id": self.tenant_1.id, "id": 1}, {"id"}),
            ({"pk": (self.tenant_1.id, 1)}, {"id"}),
            # 1, 1, {"tenant", "id"}
            ({"tenant": self.tenant_1, "id": 1}, {"tenant", "id"}),
            ({"tenant_id": self.tenant_1.id, "id": 1}, {"tenant", "id"}),
            ({"pk": (self.tenant_1.id, 1)}, {"tenant", "id"}),
        )

        for kwargs, exclude in test_cases:
            with self.subTest(kwargs):
                kwargs["email"] = "user0004@example.com"
                User(**kwargs).full_clean(exclude=exclude)