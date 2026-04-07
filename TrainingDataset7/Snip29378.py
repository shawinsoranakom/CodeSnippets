def test_totally_ordered_none(self):
        qs = Author.objects.order_by().none()
        self.assertIs(qs.totally_ordered, False)
        qs = Author.objects.order_by("pk").none()
        self.assertIs(qs.totally_ordered, True)