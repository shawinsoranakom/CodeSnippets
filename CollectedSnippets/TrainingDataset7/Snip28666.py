def test_multiple_inheritance_cannot_shadow_concrete_inherited_field(self):
        class ConcreteParent(models.Model):
            name = models.CharField(max_length=255)

        class AbstractParent(models.Model):
            name = models.IntegerField()

            class Meta:
                abstract = True

        class FirstChild(ConcreteParent, AbstractParent):
            pass

        class AnotherChild(AbstractParent, ConcreteParent):
            pass

        self.assertIsInstance(FirstChild._meta.get_field("name"), models.CharField)
        self.assertEqual(
            AnotherChild.check(),
            [
                Error(
                    "The field 'name' clashes with the field 'name' "
                    "from model 'model_inheritance.concreteparent'.",
                    obj=AnotherChild._meta.get_field("name"),
                    id="models.E006",
                )
            ],
        )