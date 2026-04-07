def test_add_implementation(self):
        class MySum(Sum):
            pass

        # test completely changing how the output is rendered
        def lower_case_function_override(self, compiler, connection):
            sql, params = compiler.compile(self.source_expressions[0])
            substitutions = {
                "function": self.function.lower(),
                "expressions": sql,
                "distinct": "",
                "filter": "",
                "order_by": "",
            }
            substitutions.update(self.extra)
            return self.template % substitutions, params

        setattr(MySum, "as_" + connection.vendor, lower_case_function_override)

        qs = Book.objects.annotate(
            sums=MySum(
                F("rating") + F("pages") + F("price"), output_field=IntegerField()
            )
        )
        self.assertEqual(str(qs.query).count("sum("), 1)
        b1 = qs.get(pk=self.b4.pk)
        self.assertEqual(b1.sums, 383)

        # test changing the dict and delegating
        def lower_case_function_super(self, compiler, connection):
            self.extra["function"] = self.function.lower()
            return super(MySum, self).as_sql(compiler, connection)

        setattr(MySum, "as_" + connection.vendor, lower_case_function_super)

        qs = Book.objects.annotate(
            sums=MySum(
                F("rating") + F("pages") + F("price"), output_field=IntegerField()
            )
        )
        self.assertEqual(str(qs.query).count("sum("), 1)
        b1 = qs.get(pk=self.b4.pk)
        self.assertEqual(b1.sums, 383)

        # test overriding all parts of the template
        def be_evil(self, compiler, connection):
            substitutions = {
                "function": "MAX",
                "expressions": "2",
                "distinct": "",
                "filter": "",
                "order_by": "",
            }
            substitutions.update(self.extra)
            return self.template % substitutions, ()

        setattr(MySum, "as_" + connection.vendor, be_evil)

        qs = Book.objects.annotate(
            sums=MySum(
                F("rating") + F("pages") + F("price"), output_field=IntegerField()
            )
        )
        self.assertEqual(str(qs.query).count("MAX("), 1)
        b1 = qs.get(pk=self.b4.pk)
        self.assertEqual(b1.sums, 2)