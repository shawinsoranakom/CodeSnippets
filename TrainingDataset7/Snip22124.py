def test_conditional_expression_lhs_contains_relation_name(self):
        qs = Book.objects.annotate(
            rel=FilteredRelation(
                "editor",
                condition=Q(number_editor__gt=1),
            )
        ).filter(rel__isnull=True)
        self.assertSequenceEqual(qs, [])