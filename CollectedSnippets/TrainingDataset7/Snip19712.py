def test_raw_missing_PK_fields(self):
        query = "SELECT tenant_id, email FROM composite_pk_user"
        msg = "Raw query must include the primary key"
        with self.assertRaisesMessage(FieldDoesNotExist, msg):
            list(User.objects.raw(query))