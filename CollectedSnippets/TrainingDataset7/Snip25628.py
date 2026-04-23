def test_invalid_to_argument_with_through(self):
        class Foo(models.Model):
            pass

        class Bar(models.Model):
            foos = models.ManyToManyField(
                to="Fo",
                through="FooBar",
                through_fields=("bar", "foo"),
            )

        class FooBar(models.Model):
            foo = models.ForeignKey("Foo", on_delete=models.CASCADE)
            bar = models.ForeignKey("Bar", on_delete=models.CASCADE)

        field = Bar._meta.get_field("foos")

        self.assertEqual(
            field.check(from_model=Bar),
            [
                Error(
                    "Field defines a relation with model 'Fo', "
                    "which is either not installed, or is abstract.",
                    obj=field,
                    id="fields.E300",
                ),
                Error(
                    "The model is used as an intermediate model by "
                    "'invalid_models_tests.Bar.foos', "
                    "but it does not have a foreign key to 'Bar' "
                    "or 'invalid_models_tests.Fo'.",
                    obj=FooBar,
                    id="fields.E336",
                ),
                Error(
                    "'FooBar.foo' is not a foreign key to 'Fo'.",
                    obj=field,
                    id="fields.E339",
                ),
            ],
        )