def test_composite_pk_in_fields(self):
        user_fields = {f.name for f in User._meta.get_fields()}
        self.assertTrue({"pk", "tenant", "id"}.issubset(user_fields))

        comment_fields = {f.name for f in Comment._meta.get_fields()}
        self.assertTrue({"pk", "tenant", "id"}.issubset(comment_fields))