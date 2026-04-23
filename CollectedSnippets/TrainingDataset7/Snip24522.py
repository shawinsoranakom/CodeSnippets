def test_model_inheritance(self):
        "Tests LayerMapping on inherited models. See #12093."
        icity_mapping = {
            "name": "Name",
            "population": "Population",
            "density": "Density",
            "point": "POINT",
            "dt": "Created",
        }
        # Parent model has geometry field.
        lm1 = LayerMapping(ICity1, city_shp, icity_mapping)
        lm1.save()

        # Grandparent has geometry field.
        lm2 = LayerMapping(ICity2, city_shp, icity_mapping)
        lm2.save()

        self.assertEqual(6, ICity1.objects.count())
        self.assertEqual(3, ICity2.objects.count())