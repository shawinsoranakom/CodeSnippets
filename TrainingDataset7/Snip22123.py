def test_conditional_expression_lhs_startswith_relation_name(self):
        qs = Book.objects.annotate(
            rel=FilteredRelation(
                "editor",
                condition=Q(editor_number__gt=1),
            )
        ).filter(rel__isnull=True)
        self.assertSequenceEqual(qs, [])