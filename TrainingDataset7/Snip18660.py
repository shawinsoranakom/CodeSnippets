def perform_query():
            # Generates SQL that is known to be problematic from a server-side
            # binding perspective as the parametrized ORDER BY clause doesn't
            # use the same binding parameter as the SELECT clause.
            qs = (
                Person.objects.order_by(
                    models.functions.Coalesce("first_name", models.Value(""))
                )
                .distinct()
                .iterator()
            )
            self.assertSequenceEqual(list(qs), [self.p0, self.p1])