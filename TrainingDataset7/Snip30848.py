def test_fk_reuse(self):
        qs = Annotation.objects.filter(tag__name="foo").filter(tag__name="bar")
        self.assertEqual(str(qs.query).count("JOIN"), 1)