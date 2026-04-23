def test_reverse_foreign_key(self):
        class AbstractBase(models.Model):
            foo = models.CharField(max_length=100)

            class Meta:
                abstract = True

        class Descendant(AbstractBase):
            pass

        class Foo(models.Model):
            foo = models.ForeignKey(Descendant, models.CASCADE, related_name="foo")

        self.assertEqual(
            Foo._meta.get_field("foo").check(),
            [
                Error(
                    "Reverse accessor 'Descendant.foo' for "
                    "'model_inheritance.Foo.foo' clashes with field name "
                    "'model_inheritance.Descendant.foo'.",
                    hint=(
                        "Rename field 'model_inheritance.Descendant.foo', or "
                        "add/change a related_name argument to the definition "
                        "for field 'model_inheritance.Foo.foo'."
                    ),
                    obj=Foo._meta.get_field("foo"),
                    id="fields.E302",
                ),
                Error(
                    "Reverse query name for 'model_inheritance.Foo.foo' "
                    "clashes with field name "
                    "'model_inheritance.Descendant.foo'.",
                    hint=(
                        "Rename field 'model_inheritance.Descendant.foo', or "
                        "add/change a related_name argument to the definition "
                        "for field 'model_inheritance.Foo.foo'."
                    ),
                    obj=Foo._meta.get_field("foo"),
                    id="fields.E303",
                ),
            ],
        )