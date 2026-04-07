def test_outerref_mixed_case_table_name(self):
        inner = Result.objects.filter(result_time__gte=OuterRef("experiment__assigned"))
        outer = Result.objects.filter(pk__in=Subquery(inner.values("pk")))
        self.assertFalse(outer.exists())