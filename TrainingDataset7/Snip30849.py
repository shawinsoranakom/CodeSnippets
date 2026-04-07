def test_fk_reuse_select_related(self):
        qs = Annotation.objects.filter(tag__name="foo").select_related("tag")
        self.assertEqual(str(qs.query).count("JOIN"), 1)