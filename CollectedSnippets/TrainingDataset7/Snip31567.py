def test_access_fks_with_select_related(self):
        """
        A select_related() call will fill in those related objects without any
        extra queries
        """
        with self.assertNumQueries(1):
            person = Species.objects.select_related(
                "genus__family__order__klass__phylum__kingdom__domain"
            ).get(name="sapiens")
            domain = person.genus.family.order.klass.phylum.kingdom.domain
            self.assertEqual(domain.name, "Eukaryota")