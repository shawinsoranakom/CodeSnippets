def test_repr(self):
        g = GeoIP2()
        m = g._metadata
        version = f"{m.binary_format_major_version}.{m.binary_format_minor_version}"
        self.assertEqual(repr(g), f"<GeoIP2 [v{version}] _path='{g._path}'>")