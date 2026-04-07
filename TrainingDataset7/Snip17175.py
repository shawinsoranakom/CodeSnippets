def test_aggregate_over_full_expression_annotation(self):
        qs = Book.objects.annotate(
            selected=ExpressionWrapper(~Q(pk__in=[]), output_field=BooleanField()),
        ).aggregate(selected__sum=Sum(Cast("selected", IntegerField())))
        self.assertEqual(qs["selected__sum"], Book.objects.count())