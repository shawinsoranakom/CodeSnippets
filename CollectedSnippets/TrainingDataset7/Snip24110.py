def test_band_statistics(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            rs_path = os.path.join(tmp_dir, "raster.tif")
            shutil.copyfile(self.rs_path, rs_path)
            rs = GDALRaster(rs_path)
            band = rs.bands[0]
            pam_file = rs_path + ".aux.xml"
            smin, smax, smean, sstd = band.statistics(approximate=True)
            self.assertEqual(smin, 0)
            self.assertEqual(smax, 9)
            self.assertAlmostEqual(smean, 2.842331288343558)
            self.assertAlmostEqual(sstd, 2.3965567248965356)

            smin, smax, smean, sstd = band.statistics(approximate=False, refresh=True)
            self.assertEqual(smin, 0)
            self.assertEqual(smax, 9)
            self.assertAlmostEqual(smean, 2.828326634228898)
            self.assertAlmostEqual(sstd, 2.4260526986669095)

            self.assertEqual(band.min, 0)
            self.assertEqual(band.max, 9)
            self.assertAlmostEqual(band.mean, 2.828326634228898)
            self.assertAlmostEqual(band.std, 2.4260526986669095)

            # Statistics are persisted into PAM file on band close
            rs = band = None
            self.assertTrue(os.path.isfile(pam_file))