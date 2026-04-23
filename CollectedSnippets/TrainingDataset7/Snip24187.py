def test_assvg(self):
        with self.assertRaises(TypeError):
            City.objects.annotate(svg=functions.AsSVG("point", precision="foo"))
        # SELECT AsSVG(geoapp_city.point, 0, 8) FROM geoapp_city
        # WHERE name = 'Pueblo';
        svg1 = 'cx="-104.609252" cy="-38.255001"'
        # Even though relative, only one point so it's practically the same
        # except for the 'c' letter prefix on the x,y values.
        svg2 = svg1.replace("c", "")
        self.assertEqual(
            svg1,
            City.objects.annotate(svg=functions.AsSVG("point")).get(name="Pueblo").svg,
        )
        self.assertEqual(
            svg2,
            City.objects.annotate(svg=functions.AsSVG("point", relative=5))
            .get(name="Pueblo")
            .svg,
        )