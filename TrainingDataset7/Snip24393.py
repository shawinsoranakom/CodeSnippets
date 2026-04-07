def test_geos_version_tuple(self):
        versions = (
            (b"3.0.0rc4-CAPI-1.3.3", (3, 0, 0)),
            (b"3.0.0-CAPI-1.4.1", (3, 0, 0)),
            (b"3.4.0dev-CAPI-1.8.0", (3, 4, 0)),
            (b"3.4.0dev-CAPI-1.8.0 r0", (3, 4, 0)),
            (b"3.6.2-CAPI-1.10.2 4d2925d6", (3, 6, 2)),
        )
        for version_string, version_tuple in versions:
            with self.subTest(version_string=version_string):
                with mock.patch(
                    "django.contrib.gis.geos.libgeos.geos_version",
                    lambda: version_string,
                ):
                    self.assertEqual(geos_version_tuple(), version_tuple)