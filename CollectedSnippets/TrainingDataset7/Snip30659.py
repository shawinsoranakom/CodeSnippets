def test_order_by_reverse_fk(self):
        # It is possible to order by reverse of foreign key, although that can
        # lead to duplicate results.
        c1 = SimpleCategory.objects.create(name="category1")
        c2 = SimpleCategory.objects.create(name="category2")
        CategoryItem.objects.create(category=c1)
        CategoryItem.objects.create(category=c2)
        CategoryItem.objects.create(category=c1)
        self.assertSequenceEqual(
            SimpleCategory.objects.order_by("categoryitem", "pk"), [c1, c2, c1]
        )