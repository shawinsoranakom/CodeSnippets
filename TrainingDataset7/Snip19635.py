def test_outer_ref_not_composite_pk(self):
        subquery = Comment.objects.filter(pk=OuterRef("id")).values("id")[:1]
        queryset = Comment.objects.filter(id=Subquery(subquery))

        msg = "Composite field lookups only work with composite expressions."
        with self.assertRaisesMessage(ValueError, msg):
            self.assertEqual(queryset.count(), 5)