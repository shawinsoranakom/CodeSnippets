def test_field_name_clash_with_child_accessor(self):
        class Parent(models.Model):
            pass

        class Child(Parent):
            child = models.CharField(max_length=100)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "The field 'child' clashes with the field "
                    "'child' from model 'invalid_models_tests.parent'.",
                    obj=Child._meta.get_field("child"),
                    id="models.E006",
                )
            ],
        )