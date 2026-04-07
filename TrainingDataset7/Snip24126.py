def test09_authority(self):
        "Testing the authority name & code routines."
        for s in srlist:
            if hasattr(s, "auth"):
                srs = SpatialReference(s.wkt)
                for target, tup in s.auth.items():
                    self.assertEqual(tup[0], srs.auth_name(target))
                    self.assertEqual(tup[1], srs.auth_code(target))