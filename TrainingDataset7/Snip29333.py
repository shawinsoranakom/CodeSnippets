def test_set_order(self):
        e = Entity.objects.create()
        d = Dimension.objects.create(entity=e)
        c1 = d.component_set.create()
        c2 = d.component_set.create()
        d.set_component_order([c1.id, c2.id])
        self.assertQuerySetEqual(
            d.component_set.all(), [c1.id, c2.id], attrgetter("pk")
        )