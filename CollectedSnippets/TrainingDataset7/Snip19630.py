def test_outer_ref_pk_filter_on_pk_exact(self):
        subquery = Subquery(User.objects.filter(pk=OuterRef("pk")).values("pk")[:1])
        qs = Comment.objects.filter(pk=subquery)
        self.assertEqual(qs.count(), 2)