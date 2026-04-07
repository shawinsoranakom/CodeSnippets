def test_override_private_field_with_attr(self):
        class AbstractBase(models.Model):
            content_type = models.ForeignKey(
                ContentType, on_delete=models.SET_NULL, null=True, blank=True
            )
            object_id = models.PositiveIntegerField(null=True, blank=True)
            related_object = GenericForeignKey("content_type", "object_id")

            class Meta:
                abstract = True

        class Descendant(AbstractBase):
            related_object = None

        class Mixin:
            related_object = None

        class MultiDescendant(Mixin, AbstractBase):
            pass

        with self.assertRaises(FieldDoesNotExist):
            Descendant._meta.get_field("related_object")

        with self.assertRaises(FieldDoesNotExist):
            MultiDescendant._meta.get_field("related_object")