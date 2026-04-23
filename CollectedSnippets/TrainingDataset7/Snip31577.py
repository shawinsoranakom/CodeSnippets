def test_chaining(self):
        parent_1, parent_2 = Species.objects.all()[:2]
        HybridSpecies.objects.create(
            name="hybrid", parent_1=parent_1, parent_2=parent_2
        )
        queryset = HybridSpecies.objects.select_related("parent_1").select_related(
            "parent_2"
        )
        with self.assertNumQueries(1):
            obj = queryset[0]
            self.assertEqual(obj.parent_1, parent_1)
            self.assertEqual(obj.parent_2, parent_2)