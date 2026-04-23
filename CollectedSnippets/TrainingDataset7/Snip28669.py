def test_cannot_override_indirect_abstract_field(self):
        class AbstractBase(models.Model):
            name = models.CharField(max_length=30)

            class Meta:
                abstract = True

        class ConcreteDescendant(AbstractBase):
            pass

        msg = (
            "Local field 'name' in class 'Descendant' clashes with field of "
            "the same name from base class 'ConcreteDescendant'."
        )
        with self.assertRaisesMessage(FieldError, msg):

            class Descendant(ConcreteDescendant):
                name = models.IntegerField()