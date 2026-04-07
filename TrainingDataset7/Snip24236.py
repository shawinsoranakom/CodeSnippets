def test_update(self):
        "Testing QuerySet.update() (#10411)."
        pueblo = City.objects.get(name="Pueblo")
        bak = pueblo.point.clone()
        pueblo.point.y += 0.005
        pueblo.point.x += 0.005

        City.objects.filter(name="Pueblo").update(point=pueblo.point)
        pueblo.refresh_from_db()
        self.assertAlmostEqual(bak.y + 0.005, pueblo.point.y, 6)
        self.assertAlmostEqual(bak.x + 0.005, pueblo.point.x, 6)
        City.objects.filter(name="Pueblo").update(point=bak)
        pueblo.refresh_from_db()
        self.assertAlmostEqual(bak.y, pueblo.point.y, 6)
        self.assertAlmostEqual(bak.x, pueblo.point.x, 6)