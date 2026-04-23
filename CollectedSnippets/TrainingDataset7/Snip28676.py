def test_override_one2one_relation_auto_field_clashes(self):
        class ConcreteParent(models.Model):
            name = models.CharField(max_length=255)

        class AbstractParent(models.Model):
            name = models.IntegerField()

            class Meta:
                abstract = True

        msg = (
            "Auto-generated field 'concreteparent_ptr' in class 'Descendant' "
            "for parent_link to base class 'ConcreteParent' clashes with "
            "declared field of the same name."
        )
        with self.assertRaisesMessage(FieldError, msg):

            class Descendant(ConcreteParent, AbstractParent):
                concreteparent_ptr = models.CharField(max_length=30)