def test_fk_reuse_annotation(self):
        qs = Annotation.objects.filter(tag__name="foo").annotate(cnt=Count("tag__name"))
        self.assertEqual(str(qs.query).count("JOIN"), 1)