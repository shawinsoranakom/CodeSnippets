def test_order_by(self):
        self.generate()
        things = [t.when for t in Thing.objects.order_by("when")]
        self.assertEqual(things, ["a", "h"])