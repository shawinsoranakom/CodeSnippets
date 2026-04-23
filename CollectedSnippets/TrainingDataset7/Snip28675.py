def test_multi_inheritance_field_clashes(self):
        class AbstractBase(models.Model):
            name = models.CharField(max_length=30)

            class Meta:
                abstract = True

        class ConcreteBase(AbstractBase):
            pass

        class AbstractDescendant(ConcreteBase):
            class Meta:
                abstract = True

        class ConcreteDescendant(AbstractDescendant):
            name = models.CharField(max_length=100)

        self.assertEqual(
            ConcreteDescendant.check(),
            [
                Error(
                    "The field 'name' clashes with the field 'name' from "
                    "model 'model_inheritance.concretebase'.",
                    obj=ConcreteDescendant._meta.get_field("name"),
                    id="models.E006",
                )
            ],
        )