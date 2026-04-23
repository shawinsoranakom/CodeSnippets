def test_fk_reuse_disjunction(self):
        qs = Annotation.objects.filter(Q(tag__name="foo") | Q(tag__name="bar"))
        self.assertEqual(str(qs.query).count("JOIN"), 1)