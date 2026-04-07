def test_field_error_values_list(self):
        # see #23443
        msg = (
            "Cannot resolve keyword %r into field. Join on 'name' not permitted."
            % "foo"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Tag.objects.values_list("name__foo")