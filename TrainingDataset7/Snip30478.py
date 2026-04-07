def test_union_slice_index(self):
        Celebrity.objects.create(name="Famous")
        c1 = Celebrity.objects.create(name="Very famous")

        qs1 = Celebrity.objects.filter(name="nonexistent")
        qs2 = Celebrity.objects.all()
        combined_qs = qs1.union(qs2).order_by("name")
        self.assertEqual(combined_qs[1], c1)