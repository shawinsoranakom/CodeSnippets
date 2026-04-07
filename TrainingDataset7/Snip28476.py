def test_many_to_many(self):
        """Data for a ManyToManyField is a list rather than a lazy QuerySet."""
        blue = Color.objects.create(name="blue")
        red = Color.objects.create(name="red")
        item = ColorfulItem.objects.create()
        item.colors.set([blue])
        data = model_to_dict(item)["colors"]
        self.assertEqual(data, [blue])
        item.colors.set([red])
        # If data were a QuerySet, it would be reevaluated here and give "red"
        # instead of the original value.
        self.assertEqual(data, [blue])