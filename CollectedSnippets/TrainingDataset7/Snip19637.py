def test_filter_by_tuple_containing_expression(self):
        pk_lookup = (self.comment_1.tenant.id, (Value(self.comment_1.id) + 1) - 1)
        for lookup in ({"pk": pk_lookup}, {"pk__in": [pk_lookup]}):
            with self.subTest(lookup=lookup):
                qs = Comment.objects.filter(**lookup)
                self.assertEqual(qs.get(), self.comment_1)