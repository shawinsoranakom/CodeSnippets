def test_full_clean_failure(self):
        e_tenant_and_id = "User with this Tenant and Id already exists."
        e_id = "User with this Id already exists."
        test_cases = (
            # 1, 1, {}
            ({"tenant": self.tenant_1, "id": 1}, {}, (e_tenant_and_id, e_id)),
            ({"tenant_id": self.tenant_1.id, "id": 1}, {}, (e_tenant_and_id, e_id)),
            ({"pk": (self.tenant_1.id, 1)}, {}, (e_tenant_and_id, e_id)),
            # 2, 1, {}
            ({"tenant": self.tenant_2, "id": 1}, {}, (e_id,)),
            ({"tenant_id": self.tenant_2.id, "id": 1}, {}, (e_id,)),
            ({"pk": (self.tenant_2.id, 1)}, {}, (e_id,)),
            # 1, 1, {"tenant"}
            ({"tenant": self.tenant_1, "id": 1}, {"tenant"}, (e_id,)),
            ({"tenant_id": self.tenant_1.id, "id": 1}, {"tenant"}, (e_id,)),
            ({"pk": (self.tenant_1.id, 1)}, {"tenant"}, (e_id,)),
        )

        for kwargs, exclude, messages in test_cases:
            with self.subTest(kwargs):
                with self.assertRaises(ValidationError) as ctx:
                    kwargs["email"] = "user0004@example.com"
                    User(**kwargs).full_clean(exclude=exclude)

                self.assertSequenceEqual(ctx.exception.messages, messages)