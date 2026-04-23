def test_clash_parent_link(self):
        class Parent(models.Model):
            pass

        class Child(Parent):
            other_parent = models.OneToOneField(Parent, models.CASCADE)

        errors = [
            (
                "fields.E304",
                "accessor",
                " 'Parent.child'",
                "parent_ptr",
                "other_parent",
            ),
            ("fields.E305", "query name", "", "parent_ptr", "other_parent"),
            (
                "fields.E304",
                "accessor",
                " 'Parent.child'",
                "other_parent",
                "parent_ptr",
            ),
            ("fields.E305", "query name", "", "other_parent", "parent_ptr"),
        ]
        self.assertEqual(
            Child.check(),
            [
                Error(
                    "Reverse %s%s for 'invalid_models_tests.Child.%s' clashes with "
                    "reverse %s for 'invalid_models_tests.Child.%s'."
                    % (attr, rel_name, field_name, attr, clash_name),
                    hint=(
                        "Add or change a related_name argument to the definition "
                        "for 'invalid_models_tests.Child.%s' or "
                        "'invalid_models_tests.Child.%s'." % (field_name, clash_name)
                    ),
                    obj=Child._meta.get_field(field_name),
                    id=error_id,
                )
                for error_id, attr, rel_name, field_name, clash_name in errors
            ],
        )