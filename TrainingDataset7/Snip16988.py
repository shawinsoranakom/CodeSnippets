def test_arguments_must_be_expressions(self):
        msg = "QuerySet.aggregate() received non-expression(s): %s."
        with self.assertRaisesMessage(TypeError, msg % FloatField()):
            Book.objects.aggregate(FloatField())
        with self.assertRaisesMessage(TypeError, msg % True):
            Book.objects.aggregate(is_book=True)
        with self.assertRaisesMessage(
            TypeError, msg % ", ".join([str(FloatField()), "True"])
        ):
            Book.objects.aggregate(FloatField(), Avg("price"), is_book=True)