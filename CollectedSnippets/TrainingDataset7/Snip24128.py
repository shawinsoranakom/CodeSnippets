def test11_wellknown(self):
        "Testing Well Known Names of Spatial References."
        for s in well_known:
            srs = SpatialReference(s.wk)
            self.assertEqual(s.name, srs.name)
            for tup in s.attrs:
                if len(tup) == 2:
                    key = tup[0]
                    exp = tup[1]
                elif len(tup) == 3:
                    key = tup[:2]
                    exp = tup[2]
                self.assertEqual(srs[key], exp)