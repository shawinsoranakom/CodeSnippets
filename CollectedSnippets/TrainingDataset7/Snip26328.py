def test_set_existing_different_type(self):
        # Existing many-to-many relations remain the same for values provided
        # with a different type.
        ids = set(
            Publication.article_set.through.objects.filter(
                article__in=[self.a4, self.a3],
                publication=self.p2,
            ).values_list("id", flat=True)
        )
        self.p2.article_set.set([str(self.a4.pk), str(self.a3.pk)])
        new_ids = set(
            Publication.article_set.through.objects.filter(
                publication=self.p2,
            ).values_list("id", flat=True)
        )
        self.assertEqual(ids, new_ids)