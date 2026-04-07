def test_ticket15316_one2one_exclude_true(self):
        c = SimpleCategory.objects.create(name="cat")
        c0 = SimpleCategory.objects.create(name="cat0")
        c1 = SimpleCategory.objects.create(name="category1")

        OneToOneCategory.objects.create(category=c1, new_name="new1")
        OneToOneCategory.objects.create(category=c0, new_name="new2")

        CategoryItem.objects.create(category=c)
        ci2 = CategoryItem.objects.create(category=c0)
        ci3 = CategoryItem.objects.create(category=c1)

        qs = CategoryItem.objects.exclude(
            category__onetoonecategory__isnull=True
        ).order_by("pk")
        self.assertEqual(qs.count(), 2)
        self.assertSequenceEqual(qs, [ci2, ci3])