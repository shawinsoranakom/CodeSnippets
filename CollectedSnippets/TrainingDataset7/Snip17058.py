def test_referenced_group_by_annotation_kept(self):
        queryset = Book.objects.values(pages_mod=Mod("pages", 10)).annotate(
            mod_count=Count("*")
        )
        self.assertEqual(queryset.count(), 1)