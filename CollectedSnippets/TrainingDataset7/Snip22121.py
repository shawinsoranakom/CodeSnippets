def test_conditional_expression_rhs_contains_relation_name(self):
        qs = Book.objects.annotate(
            rel=FilteredRelation(
                "editor",
                condition=Q(id=1 * F("number_editor")),
            )
        ).filter(rel__isnull=True)
        self.assertSequenceEqual(qs, [])