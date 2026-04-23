def test_access_fks_without_select_related(self):
        """
        Normally, accessing FKs doesn't fill in related objects
        """
        with self.assertNumQueries(8):
            fly = Species.objects.get(name="melanogaster")
            domain = fly.genus.family.order.klass.phylum.kingdom.domain
            self.assertEqual(domain.name, "Eukaryota")