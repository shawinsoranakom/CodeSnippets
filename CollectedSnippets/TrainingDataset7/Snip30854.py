def test_revfk_noreuse(self):
        qs = Author.objects.filter(report__name="r4").filter(report__name="r1")
        self.assertEqual(str(qs.query).count("JOIN"), 2)