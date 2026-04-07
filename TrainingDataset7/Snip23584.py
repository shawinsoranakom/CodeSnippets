def test_join_reuse(self):
        qs = Person.objects.filter(addresses__street="foo").filter(
            addresses__street="bar"
        )
        self.assertEqual(str(qs.query).count("JOIN"), 2)