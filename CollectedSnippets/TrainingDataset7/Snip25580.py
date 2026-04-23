def test_m2m_to_m2m_with_inheritance(self):
        """Ref #22047."""

        class Target(models.Model):
            pass

        class Model(models.Model):
            children = models.ManyToManyField(
                "Child", related_name="m2m_clash", related_query_name="no_clash"
            )

        class Parent(models.Model):
            m2m_clash = models.ManyToManyField("Target")

        class Child(Parent):
            pass

        self.assertEqual(
            Model.check(),
            [
                Error(
                    "Reverse accessor 'Child.m2m_clash' for "
                    "'invalid_models_tests.Model.children' clashes with field "
                    "name 'invalid_models_tests.Child.m2m_clash'.",
                    hint=(
                        "Rename field 'invalid_models_tests.Child.m2m_clash', or "
                        "add/change a related_name argument to the definition for "
                        "field 'invalid_models_tests.Model.children'."
                    ),
                    obj=Model._meta.get_field("children"),
                    id="fields.E302",
                )
            ],
        )