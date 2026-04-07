def test_abstract_inherited_fields(self):
        """Field instances from abstract models are not equal."""

        class AbstractModel(models.Model):
            field = models.IntegerField()

            class Meta:
                abstract = True

        class InheritAbstractModel1(AbstractModel):
            pass

        class InheritAbstractModel2(AbstractModel):
            pass

        abstract_model_field = AbstractModel._meta.get_field("field")
        inherit1_model_field = InheritAbstractModel1._meta.get_field("field")
        inherit2_model_field = InheritAbstractModel2._meta.get_field("field")

        self.assertNotEqual(abstract_model_field, inherit1_model_field)
        self.assertNotEqual(abstract_model_field, inherit2_model_field)
        self.assertNotEqual(inherit1_model_field, inherit2_model_field)

        self.assertLess(abstract_model_field, inherit1_model_field)
        self.assertLess(abstract_model_field, inherit2_model_field)
        self.assertLess(inherit1_model_field, inherit2_model_field)