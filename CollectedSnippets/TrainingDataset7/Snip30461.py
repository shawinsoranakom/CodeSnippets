def test_missing_field(self):
        q = Q(description__startswith="prefix")
        msg = "Cannot resolve keyword 'description' into field."
        with self.assertRaisesMessage(FieldError, msg):
            q.check({"name": "test"})