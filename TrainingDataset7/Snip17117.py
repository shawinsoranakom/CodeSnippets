def test_empty_filter_count(self):
        self.assertEqual(
            Author.objects.filter(id__in=[]).annotate(Count("friends")).count(), 0
        )