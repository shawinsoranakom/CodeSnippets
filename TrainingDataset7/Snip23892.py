def test_get_object_or_404_queryset_attribute_error(self):
        """AttributeError raised by QuerySet.get() isn't hidden."""
        with self.assertRaisesMessage(AttributeError, "AttributeErrorManager"):
            get_object_or_404(Article.attribute_error_objects, id=42)