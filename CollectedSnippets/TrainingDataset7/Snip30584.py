def test_ticket2091(self):
        t = Tag.objects.get(name="t4")
        self.assertSequenceEqual(Item.objects.filter(tags__in=[t]), [self.i4])