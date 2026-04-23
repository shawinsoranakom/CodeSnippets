def test_utc_offset_out_of_bounds(self):
        class Edgy(tzinfo):
            def __init__(self, offset):
                self.offset = timedelta(minutes=offset)
            def utcoffset(self, dt):
                return self.offset

        cls = self.theclass
        for offset, legit in ((-1440, False),
                              (-1439, True),
                              (1439, True),
                              (1440, False)):
            if cls is time:
                t = cls(1, 2, 3, tzinfo=Edgy(offset))
            elif cls is datetime:
                t = cls(6, 6, 6, 1, 2, 3, tzinfo=Edgy(offset))
            else:
                assert 0, "impossible"
            if legit:
                aofs = abs(offset)
                h, m = divmod(aofs, 60)
                tag = "%c%02d:%02d" % (offset < 0 and '-' or '+', h, m)
                if isinstance(t, datetime):
                    t = t.timetz()
                self.assertEqual(str(t), "01:02:03" + tag)
            else:
                self.assertRaises(ValueError, str, t)