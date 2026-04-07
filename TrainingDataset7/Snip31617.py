def test_multi_table_inheritance(self):
        """Exercising select_related() with multi-table model inheritance."""
        c1 = Child.objects.create(name="child1", value=42)
        i1 = Item.objects.create(name="item1", child=c1)
        i2 = Item.objects.create(name="item2")

        self.assertSequenceEqual(
            Item.objects.select_related("child").order_by("name"),
            [i1, i2],
        )