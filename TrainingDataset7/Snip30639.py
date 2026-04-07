def test_field_with_filterable(self):
        self.assertSequenceEqual(
            Author.objects.filter(extra=self.e2),
            [self.a3, self.a4],
        )