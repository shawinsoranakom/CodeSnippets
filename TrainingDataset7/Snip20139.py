def test_custom_lookup_with_subquery(self):
        class NotEqual(models.Lookup):
            lookup_name = "ne"

            def as_sql(self, compiler, connection):
                lhs, lhs_params = self.process_lhs(compiler, connection)
                rhs, rhs_params = self.process_rhs(compiler, connection)
                # Although combining via (*lhs_params, *rhs_params) would be
                # more resilient, the "simple" way works too.
                params = lhs_params + rhs_params
                return "%s <> %s" % (lhs, rhs), params

        author = Author.objects.create(name="Isabella")

        with register_lookup(models.Field, NotEqual):
            qs = Author.objects.annotate(
                unknown_age=models.Subquery(
                    Author.objects.filter(age__isnull=True)
                    .order_by("name")
                    .values("name")[:1]
                )
            ).filter(unknown_age__ne="Plato")
            self.assertSequenceEqual(qs, [author])

            qs = Author.objects.annotate(
                unknown_age=Lower(
                    Author.objects.filter(age__isnull=True)
                    .order_by("name")
                    .values("name")[:1]
                )
            ).filter(unknown_age__ne="plato")
            self.assertSequenceEqual(qs, [author])