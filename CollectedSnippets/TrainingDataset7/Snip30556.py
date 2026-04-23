def test_names_to_path_field_error(self):
        query = Query(None)
        msg = "Cannot resolve keyword 'nonexistent' into field."
        with self.assertRaisesMessage(FieldError, msg):
            query.names_to_path(["nonexistent"], opts=None)