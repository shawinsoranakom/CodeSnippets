def test10_combine(self):
        "Testing the combination of two QuerySets (#10807)."
        buf1 = City.objects.get(name="Aurora").location.point.buffer(0.1)
        buf2 = City.objects.get(name="Kecksburg").location.point.buffer(0.1)
        qs1 = City.objects.filter(location__point__within=buf1)
        qs2 = City.objects.filter(location__point__within=buf2)
        combined = qs1 | qs2
        names = [c.name for c in combined]
        self.assertEqual(2, len(names))
        self.assertIn("Aurora", names)
        self.assertIn("Kecksburg", names)