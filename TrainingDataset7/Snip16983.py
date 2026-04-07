def test_annotated_aggregate_over_annotated_aggregate(self):
        with self.assertRaisesMessage(
            FieldError, "Cannot compute Sum('id__max'): 'id__max' is an aggregate"
        ):
            Book.objects.annotate(Max("id")).annotate(Sum("id__max"))

        class MyMax(Max):
            arity = None

            def as_sql(self, compiler, connection):
                self.set_source_expressions(self.get_source_expressions()[0:1])
                return super().as_sql(compiler, connection)

        with self.assertRaisesMessage(
            FieldError, "Cannot compute Max('id__max'): 'id__max' is an aggregate"
        ):
            Book.objects.annotate(Max("id")).annotate(my_max=MyMax("id__max", "price"))