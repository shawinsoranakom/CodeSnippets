def test_q_annotation_aggregate(self):
        self.assertEqual(Book.objects.annotate(has_pk=Q(pk__isnull=False)).count(), 6)