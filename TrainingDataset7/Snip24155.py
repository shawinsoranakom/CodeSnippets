def check_extent3d(extent3d, tol=6):
            for ref_val, ext_val in zip(ref_extent3d, extent3d):
                self.assertAlmostEqual(ref_val, ext_val, tol)