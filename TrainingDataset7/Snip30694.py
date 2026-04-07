def test_ticket_11320(self):
        qs = Tag.objects.exclude(category=None).exclude(category__name="foo")
        self.assertEqual(str(qs.query).count(" INNER JOIN "), 1)