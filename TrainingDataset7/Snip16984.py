def test_multi_arg_aggregate(self):
        class MultiArgAgg(Max):
            output_field = DecimalField()
            arity = None

            def as_sql(self, compiler, connection, **extra_context):
                copy = self.copy()
                # Most database backends do not support compiling multiple
                # arguments on the Max aggregate, and that isn't what is being
                # tested here anyway. To avoid errors, the extra argument is
                # just dropped.
                copy.set_source_expressions(
                    copy.get_source_expressions()[0:1] + [None, None]
                )

                return super(MultiArgAgg, copy).as_sql(compiler, connection)

        with self.assertRaisesMessage(TypeError, "Complex aggregates require an alias"):
            Book.objects.aggregate(MultiArgAgg("pages", "price"))

        with self.assertRaisesMessage(
            TypeError, "Complex annotations require an alias"
        ):
            Book.objects.annotate(MultiArgAgg("pages", "price"))

        Book.objects.aggregate(max_field=MultiArgAgg("pages", "price"))