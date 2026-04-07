def test_flat_values_list(self):
        qs = Number.objects.values_list("num")
        qs = qs.values_list("num", flat=True)
        self.assertSequenceEqual(qs, [72])