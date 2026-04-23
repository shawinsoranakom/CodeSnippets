def test_none_clears_list(self):
        queryset = Species.objects.select_related("genus").select_related(None)
        self.assertIs(queryset.query.select_related, False)