def test_hasm(self):
        pnt_xym = fromstr("POINT M (5 23 8)")
        self.assertTrue(pnt_xym.hasm)
        pnt_xyzm = fromstr("POINT (5 23 8 0)")
        self.assertTrue(pnt_xyzm.hasm)