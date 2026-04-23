def test_lookup_constraint_fielderror(self):
        msg = (
            "Cannot resolve keyword 'unknown_field' into field. Choices are: "
            "annotation, category, category_id, children, id, item, "
            "managedmodel, name, note, parent, parent_id"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Tag.objects.filter(unknown_field__name="generic")