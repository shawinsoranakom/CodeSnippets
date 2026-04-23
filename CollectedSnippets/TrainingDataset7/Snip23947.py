def test_property_attribute_without_setter_kwargs(self):
        msg = (
            "Cannot resolve keyword 'name_in_all_caps' into field. Choices are: id, "
            "name, tags"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Thing.objects.update_or_create(
                name_in_all_caps="FRANK", defaults={"name": "Frank"}
            )