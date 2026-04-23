def test_only_with_select_related(self):
        # Test for #17485.
        item = SimpleItem.objects.create(name="first", value=47)
        feature = Feature.objects.create(item=item)
        SpecialFeature.objects.create(feature=feature)

        qs = Feature.objects.only("item__name").select_related("item")
        self.assertEqual(len(qs), 1)

        qs = SpecialFeature.objects.only("feature__item__name").select_related(
            "feature__item"
        )
        self.assertEqual(len(qs), 1)