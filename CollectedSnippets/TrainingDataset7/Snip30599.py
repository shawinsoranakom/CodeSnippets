def test_ticket9926(self):
        self.assertSequenceEqual(
            Tag.objects.select_related("parent", "category").order_by("name"),
            [self.t1, self.t2, self.t3, self.t4, self.t5],
        )
        self.assertSequenceEqual(
            Tag.objects.select_related("parent", "parent__category").order_by("name"),
            [self.t1, self.t2, self.t3, self.t4, self.t5],
        )