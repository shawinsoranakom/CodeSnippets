def test_exact_booleanfield_annotation(self):
        # MySQL ignores indexes with boolean fields unless they're compared
        # directly to a boolean value.
        qs = Author.objects.annotate(
            case=Case(
                When(alias="a1", then=True),
                default=False,
                output_field=BooleanField(),
            )
        ).filter(case=True)
        self.assertSequenceEqual(qs, [self.au1])
        self.assertIn(" = True", str(qs.query))

        qs = Author.objects.annotate(
            wrapped=ExpressionWrapper(Q(alias="a1"), output_field=BooleanField()),
        ).filter(wrapped=True)
        self.assertSequenceEqual(qs, [self.au1])
        self.assertIn(" = True", str(qs.query))
        # EXISTS(...) shouldn't be compared to a boolean value.
        qs = Author.objects.annotate(
            exists=Exists(Author.objects.filter(alias="a1", pk=OuterRef("pk"))),
        ).filter(exists=True)
        self.assertSequenceEqual(qs, [self.au1])
        self.assertNotIn(" = True", str(qs.query))