def test_order_by_extra(self):
        self.assertIs(Annotation.objects.extra(order_by=["id"]).ordered, True)