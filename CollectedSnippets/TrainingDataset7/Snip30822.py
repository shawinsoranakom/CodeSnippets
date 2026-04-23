def test_ticket15786(self):
        c1 = SimpleCategory.objects.create(name="c1")
        c2 = SimpleCategory.objects.create(name="c2")
        OneToOneCategory.objects.create(category=c1)
        OneToOneCategory.objects.create(category=c2)
        rel = CategoryRelationship.objects.create(first=c1, second=c2)
        self.assertEqual(
            CategoryRelationship.objects.exclude(
                first__onetoonecategory=F("second__onetoonecategory")
            ).get(),
            rel,
        )