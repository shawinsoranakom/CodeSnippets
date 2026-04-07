def test_fk_reuse_order_by(self):
        qs = Annotation.objects.filter(tag__name="foo").order_by("tag__name")
        self.assertEqual(str(qs.query).count("JOIN"), 1)