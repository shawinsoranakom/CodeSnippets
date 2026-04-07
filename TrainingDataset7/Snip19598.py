def test_delete_without_pk(self):
        msg = (
            "Comment object can't be deleted because its pk attribute is set "
            "to None."
        )

        with self.assertRaisesMessage(ValueError, msg):
            Comment().delete()
        with self.assertRaisesMessage(ValueError, msg):
            Comment(tenant_id=1).delete()
        with self.assertRaisesMessage(ValueError, msg):
            Comment(id=1).delete()