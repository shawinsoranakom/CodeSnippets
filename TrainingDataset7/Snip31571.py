def test_select_related_with_extra(self):
        s = (
            Species.objects.all()
            .select_related()
            .extra(select={"a": "select_related_species.id + 10"})[0]
        )
        self.assertEqual(s.id + 10, s.a)