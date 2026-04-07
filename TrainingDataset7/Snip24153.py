def test_scale(self):
        """
        Testing Scale() function on Z values.
        """
        self._load_city_data()
        # Mapping of City name to reference Z values.
        zscales = (-3, 4, 23)
        for zscale in zscales:
            for city in City3D.objects.annotate(scale=Scale("point", 1.0, 1.0, zscale)):
                self.assertEqual(city_dict[city.name][2] * zscale, city.scale.z)