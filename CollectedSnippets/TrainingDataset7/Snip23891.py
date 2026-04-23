def test_bad_class(self):
        # Given an argument klass that is not a Model, Manager, or Queryset
        # raises a helpful ValueError message
        msg = (
            "First argument to get_object_or_404() must be a Model, Manager, or "
            "QuerySet, not 'str'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            get_object_or_404("Article", title__icontains="Run")

        class CustomClass:
            pass

        msg = (
            "First argument to get_object_or_404() must be a Model, Manager, or "
            "QuerySet, not 'CustomClass'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            get_object_or_404(CustomClass, title__icontains="Run")

        # Works for lists too
        msg = (
            "First argument to get_list_or_404() must be a Model, Manager, or "
            "QuerySet, not 'list'."
        )
        with self.assertRaisesMessage(ValueError, msg):
            get_list_or_404([Article], title__icontains="Run")