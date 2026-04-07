def test_shadowed_fkey_id(self):
        class Foo(models.Model):
            pass

        class AbstractBase(models.Model):
            foo = models.ForeignKey(Foo, models.CASCADE)

            class Meta:
                abstract = True

        class Descendant(AbstractBase):
            foo_id = models.IntegerField()

        self.assertEqual(
            Descendant.check(),
            [
                Error(
                    "The field 'foo_id' clashes with the field 'foo' "
                    "from model 'model_inheritance.descendant'.",
                    obj=Descendant._meta.get_field("foo_id"),
                    id="models.E006",
                )
            ],
        )