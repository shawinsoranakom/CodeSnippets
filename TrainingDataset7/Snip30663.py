def test_ticket15316_exclude_false(self):
        c1 = SimpleCategory.objects.create(name="category1")
        c2 = SpecialCategory.objects.create(
            name="named category1", special_name="special1"
        )
        c3 = SpecialCategory.objects.create(
            name="named category2", special_name="special2"
        )

        ci1 = CategoryItem.objects.create(category=c1)
        CategoryItem.objects.create(category=c2)
        CategoryItem.objects.create(category=c3)

        qs = CategoryItem.objects.exclude(category__specialcategory__isnull=False)
        self.assertEqual(qs.count(), 1)
        self.assertSequenceEqual(qs, [ci1])