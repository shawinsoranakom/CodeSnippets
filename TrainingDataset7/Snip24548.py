def test_verbose_name_arg(self):
        """
        RasterField should accept a positional verbose name argument.
        """
        self.assertEqual(
            RasterModel._meta.get_field("rast").verbose_name, "A Verbose Raster Name"
        )