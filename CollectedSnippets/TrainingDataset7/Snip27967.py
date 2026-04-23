def test_negative_values(self):
        p = PositiveIntegerModel.objects.create(value=0)
        p.value = models.F("value") - 1
        with self.assertRaises(IntegrityError):
            p.save()