def test_revo2o_reuse(self):
        qs = Detail.objects.filter(member__name="foo").filter(member__name="foo")
        self.assertEqual(str(qs.query).count("JOIN"), 1)