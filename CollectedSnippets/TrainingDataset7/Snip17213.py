def test_arguments_must_be_expressions(self):
        msg = "QuerySet.annotate() received non-expression(s): %s."
        with self.assertRaisesMessage(TypeError, msg % BooleanField()):
            Book.objects.annotate(BooleanField())
        with self.assertRaisesMessage(TypeError, msg % True):
            Book.objects.annotate(is_book=True)
        with self.assertRaisesMessage(
            TypeError, msg % ", ".join([str(BooleanField()), "True"])
        ):
            Book.objects.annotate(BooleanField(), Value(False), is_book=True)