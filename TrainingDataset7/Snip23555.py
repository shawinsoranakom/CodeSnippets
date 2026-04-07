def test_prefetch_related_custom_object_id(self):
        tiger = Animal.objects.create(common_name="tiger")
        cheetah = Animal.objects.create(common_name="cheetah")
        Comparison.objects.create(
            first_obj=cheetah,
            other_obj=tiger,
            comparative="faster",
        )
        Comparison.objects.create(
            first_obj=tiger,
            other_obj=cheetah,
            comparative="cooler",
        )
        qs = Comparison.objects.prefetch_related("first_obj__comparisons")
        for comparison in qs:
            self.assertSequenceEqual(
                comparison.first_obj.comparisons.all(), [comparison]
            )