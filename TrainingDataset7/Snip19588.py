def test_bulk_create_users(self):
        objs = [
            User(tenant=self.tenant, id=8291, email="user8291@example.com"),
            User(tenant_id=self.tenant.id, id=4021, email="user4021@example.com"),
            User(pk=(self.tenant.id, 8214), email="user8214@example.com"),
        ]

        obj_1, obj_2, obj_3 = User.objects.bulk_create(objs)

        self.assertEqual(obj_1.tenant_id, self.tenant.id)
        self.assertEqual(obj_1.id, 8291)
        self.assertEqual(obj_1.pk, (obj_1.tenant_id, obj_1.id))
        self.assertEqual(obj_1.email, "user8291@example.com")
        self.assertEqual(obj_2.tenant_id, self.tenant.id)
        self.assertEqual(obj_2.id, 4021)
        self.assertEqual(obj_2.pk, (obj_2.tenant_id, obj_2.id))
        self.assertEqual(obj_2.email, "user4021@example.com")
        self.assertEqual(obj_3.tenant_id, self.tenant.id)
        self.assertEqual(obj_3.id, 8214)
        self.assertEqual(obj_3.pk, (obj_3.tenant_id, obj_3.id))
        self.assertEqual(obj_3.email, "user8214@example.com")