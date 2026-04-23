def test_inheritance(self):
        f = FriendlyAuthor.objects.create(
            first_name="Wesley", last_name="Chun", dob=date(1962, 10, 28)
        )
        query = "SELECT * FROM raw_query_friendlyauthor"
        self.assertEqual([o.pk for o in FriendlyAuthor.objects.raw(query)], [f.pk])