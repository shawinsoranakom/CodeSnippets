def test_conditional_expression_rhs_startswith_relation_name(self):
        qs = Book.objects.annotate(
            rel=FilteredRelation(
                "editor",
                condition=Q(id=1 * F("editor_number")),
            )
        ).filter(rel__isnull=True)
        self.assertSequenceEqual(qs, [])