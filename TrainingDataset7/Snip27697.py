def test_serialize_zoneinfo(self):
        self.assertSerializedEqual(zoneinfo.ZoneInfo("Asia/Kolkata"))
        self.assertSerializedResultEqual(
            zoneinfo.ZoneInfo("Asia/Kolkata"),
            (
                "zoneinfo.ZoneInfo(key='Asia/Kolkata')",
                {"import zoneinfo"},
            ),
        )
        self.assertSerializedResultEqual(
            zoneinfo.ZoneInfo("Europe/Paris"),
            ("zoneinfo.ZoneInfo(key='Europe/Paris')", {"import zoneinfo"}),
        )