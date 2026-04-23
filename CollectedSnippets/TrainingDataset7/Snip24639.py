def test_del(self):
        g = GeoIP2()
        reader = g._reader
        self.assertIs(reader._db_reader.closed, False)
        del g
        self.assertIs(reader._db_reader.closed, True)