def test_annotation_exists_none_query(self):
        self.assertIs(
            Author.objects.annotate(exists=Exists(Company.objects.none()))
            .get(pk=self.a1.pk)
            .exists,
            False,
        )