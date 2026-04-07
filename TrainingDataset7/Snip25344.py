def test_inheritance_clash(self):
        class Parent(models.Model):
            f_id = models.IntegerField()

        class Target(models.Model):
            # This field doesn't result in a clash.
            f_id = models.IntegerField()

        class Child(Parent):
            # This field clashes with parent "f_id" field.
            f = models.ForeignKey(Target, models.CASCADE)

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "The field 'f' clashes with the field 'f_id' "
                    "from model 'invalid_models_tests.parent'.",
                    obj=Child._meta.get_field("f"),
                    id="models.E006",
                )
            ],
        )