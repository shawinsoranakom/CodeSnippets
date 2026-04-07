def test_ticket15316_exclude_true(self):
        c1 = SimpleCategory.objects.create(name="category1")
        c2 = SpecialCategory.objects.create(
            name="named category1", special_name="special1"
        )
        c3 = SpecialCategory.objects.create(
            name="named category2", special_name="special2"
        )

        CategoryItem.objects.create(category=c1)
        ci2 = CategoryItem.objects.create(category=c2)
        ci3 = CategoryItem.objects.create(category=c3)

        qs = CategoryItem.objects.exclude(category__specialcategory__isnull=True)
        self.assertEqual(qs.count(), 2)
        self.assertCountEqual(qs, [ci2, ci3])