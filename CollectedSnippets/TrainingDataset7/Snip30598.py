def test_ticket6981(self):
        self.assertSequenceEqual(
            Tag.objects.select_related("parent").order_by("name"),
            [self.t1, self.t2, self.t3, self.t4, self.t5],
        )