def test_bulk_create_user_with_pk_field_in_update_fields(self):
        objs = [User(tenant=self.tenant, id=8291, email="user8291@example.com")]
        msg = "bulk_create() cannot be used with primary keys in update_fields."
        with self.assertRaisesMessage(ValueError, msg):
            User.objects.bulk_create(
                objs,
                update_conflicts=True,
                update_fields=["tenant_id"],
                unique_fields=["id", "tenant_id"],
            )