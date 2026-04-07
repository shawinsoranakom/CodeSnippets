def test_exact_tags(self):
        self.assertSequenceEqual(
            OtherTypesArrayModel.objects.filter(tags=self.tags), self.objs
        )