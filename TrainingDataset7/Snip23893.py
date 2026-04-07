def test_get_list_or_404_queryset_attribute_error(self):
        """AttributeError raised by QuerySet.filter() isn't hidden."""
        with self.assertRaisesMessage(AttributeError, "AttributeErrorManager"):
            get_list_or_404(Article.attribute_error_objects, title__icontains="Run")