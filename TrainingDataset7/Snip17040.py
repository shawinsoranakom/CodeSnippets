def test_having_with_no_group_by(self):
        author_qs = (
            Author.objects.values(static_value=Value("static-value"))
            .annotate(sum=Sum("age"))
            .filter(sum__gte=0)
            .values_list("sum", flat=True)
        )
        self.assertEqual(list(author_qs), [337])