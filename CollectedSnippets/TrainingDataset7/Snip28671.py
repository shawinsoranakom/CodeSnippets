def test_overriding_field_removed_by_concrete_model(self):
        class AbstractModel(models.Model):
            foo = models.CharField(max_length=30)

            class Meta:
                abstract = True

        class RemovedAbstractModelField(AbstractModel):
            foo = None

        class OverrideRemovedFieldByConcreteModel(RemovedAbstractModelField):
            foo = models.CharField(max_length=50)

        self.assertEqual(
            OverrideRemovedFieldByConcreteModel._meta.get_field("foo").max_length, 50
        )