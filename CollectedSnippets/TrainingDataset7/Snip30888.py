def test_ticket_21787(self):
        sc1 = SpecialCategory.objects.create(special_name="sc1", name="sc1")
        sc2 = SpecialCategory.objects.create(special_name="sc2", name="sc2")
        sc3 = SpecialCategory.objects.create(special_name="sc3", name="sc3")
        c1 = CategoryItem.objects.create(category=sc1)
        CategoryItem.objects.create(category=sc2)
        self.assertSequenceEqual(
            SpecialCategory.objects.exclude(categoryitem__id=c1.pk).order_by("name"),
            [sc2, sc3],
        )
        self.assertSequenceEqual(
            SpecialCategory.objects.filter(categoryitem__id=c1.pk), [sc1]
        )