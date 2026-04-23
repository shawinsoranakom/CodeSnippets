def test_annotate_and_join(self):
        self.assertEqual(
            Author.objects.annotate(c=Count("friends__name"))
            .exclude(friends__name="Joe")
            .count(),
            Author.objects.count(),
        )