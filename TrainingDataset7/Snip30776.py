def test_empty_resultset_sql(self):
        # ticket #12192
        self.assertNumQueries(0, lambda: list(Number.objects.all()[1:1]))