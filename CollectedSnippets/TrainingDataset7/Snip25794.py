def test_in_bulk_values_list_flat_all(self):
        Article.objects.exclude(pk__in=[self.a1.pk, self.a2.pk]).delete()
        with ignore_warnings(category=RemovedInDjango70Warning):
            arts = Article.objects.values_list(flat=True).in_bulk()
        self.assertEqual(
            arts,
            {
                self.a1.pk: self.a1.pk,
                self.a2.pk: self.a2.pk,
            },
        )