def test_3d_hasz(self):
        """
        Make sure data is 3D and has expected Z values -- shouldn't change
        because of coordinate system.
        """
        self._load_interstate_data()
        for name, line, exp_z in interstate_data:
            interstate = Interstate3D.objects.get(name=name)
            interstate_proj = InterstateProj3D.objects.get(name=name)
            for i in [interstate, interstate_proj]:
                self.assertTrue(i.line.hasz)
                self.assertEqual(exp_z, tuple(i.line.z))

        self._load_city_data()
        for name, pnt_data in city_data:
            city = City3D.objects.get(name=name)
            # Testing both geometry and geography fields
            self.assertTrue(city.point.hasz)
            self.assertTrue(city.pointg.hasz)
            self.assertEqual(city.point.z, pnt_data[2])
            self.assertEqual(city.pointg.z, pnt_data[2])