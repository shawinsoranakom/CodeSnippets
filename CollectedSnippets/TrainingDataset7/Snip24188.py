def test_aswkb(self):
        wkb = (
            City.objects.annotate(
                wkb=functions.AsWKB(Point(1, 2, srid=4326)),
            )
            .first()
            .wkb
        )
        # WKB is either XDR or NDR encoded.
        self.assertIn(
            bytes(wkb),
            (
                b"\x00\x00\x00\x00\x01?\xf0\x00\x00\x00\x00\x00\x00@\x00\x00"
                b"\x00\x00\x00\x00\x00",
                b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xf0?\x00\x00"
                b"\x00\x00\x00\x00\x00@",
            ),
        )