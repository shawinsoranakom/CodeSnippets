def test_raster_info_accessor(self):
        infos = self.rs.info
        # Data
        info_lines = [line.strip() for line in infos.split("\n") if line.strip() != ""]
        for line in [
            "Driver: GTiff/GeoTIFF",
            "Files: {}".format(self.rs_path),
            "Size is 163, 174",
            "Origin = (511700.468070655711927,435103.377123198588379)",
            "Pixel Size = (100.000000000000000,-100.000000000000000)",
            "Metadata:",
            "AREA_OR_POINT=Area",
            "Image Structure Metadata:",
            "INTERLEAVE=BAND",
            "Band 1 Block=163x50 Type=Byte, ColorInterp=Gray",
            "NoData Value=15",
        ]:
            self.assertIn(line, info_lines)
        for line in [
            r"Upper Left  \(  511700.468,  435103.377\) "
            r'\( 82d51\'46.1\d"W, 27d55\' 1.5\d"N\)',
            r"Lower Left  \(  511700.468,  417703.377\) "
            r'\( 82d51\'52.0\d"W, 27d45\'37.5\d"N\)',
            r"Upper Right \(  528000.468,  435103.377\) "
            r'\( 82d41\'48.8\d"W, 27d54\'56.3\d"N\)',
            r"Lower Right \(  528000.468,  417703.377\) "
            r'\( 82d41\'55.5\d"W, 27d45\'32.2\d"N\)',
            r"Center      \(  519850.468,  426403.377\) "
            r'\( 82d46\'50.6\d"W, 27d50\'16.9\d"N\)',
        ]:
            self.assertRegex(infos, line)
        # CRS (skip the name because string depends on the GDAL/Proj versions).
        self.assertIn("NAD83 / Florida GDL Albers", infos)