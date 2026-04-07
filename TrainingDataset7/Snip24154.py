def test_translate(self):
        """
        Testing Translate() function on Z values.
        """
        self._load_city_data()
        ztranslations = (5.23, 23, -17)
        for ztrans in ztranslations:
            for city in City3D.objects.annotate(
                translate=Translate("point", 0, 0, ztrans)
            ):
                self.assertEqual(city_dict[city.name][2] + ztrans, city.translate.z)