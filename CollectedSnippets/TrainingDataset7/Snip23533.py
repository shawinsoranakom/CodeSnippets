def test_multiple_gfk(self):
        # Simple tests for multiple GenericForeignKeys
        # only uses one model, since the above tests should be sufficient.
        tiger = Animal.objects.create(common_name="tiger")
        cheetah = Animal.objects.create(common_name="cheetah")
        bear = Animal.objects.create(common_name="bear")

        # Create directly
        c1 = Comparison.objects.create(
            first_obj=cheetah, other_obj=tiger, comparative="faster"
        )
        c2 = Comparison.objects.create(
            first_obj=tiger, other_obj=cheetah, comparative="cooler"
        )

        # Create using GenericRelation
        c3 = tiger.comparisons.create(other_obj=bear, comparative="cooler")
        c4 = tiger.comparisons.create(other_obj=cheetah, comparative="stronger")
        self.assertSequenceEqual(cheetah.comparisons.all(), [c1])

        # Filtering works
        self.assertCountEqual(
            tiger.comparisons.filter(comparative="cooler"),
            [c2, c3],
        )

        # Filtering and deleting works
        subjective = ["cooler"]
        tiger.comparisons.filter(comparative__in=subjective).delete()
        self.assertCountEqual(Comparison.objects.all(), [c1, c4])

        # If we delete cheetah, Comparisons with cheetah as 'first_obj' will be
        # deleted since Animal has an explicit GenericRelation to Comparison
        # through first_obj. Comparisons with cheetah as 'other_obj' will not
        # be deleted.
        cheetah.delete()
        self.assertSequenceEqual(Comparison.objects.all(), [c4])