def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_floor=Floor("f1"), f2_floor=Floor("f2")
        ).first()
        self.assertIsInstance(obj.f1_floor, float)
        self.assertIsInstance(obj.f2_floor, float)
        self.assertEqual(obj.f1_floor, math.floor(obj.f1))
        self.assertEqual(obj.f2_floor, math.floor(obj.f2))