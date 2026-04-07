def test_no_database_file(self):
        invalid_path = pathlib.Path(__file__).parent.joinpath("data/invalid").resolve()
        msg = "Path must be a valid database or directory containing databases."
        with self.assertRaisesMessage(GeoIP2Exception, msg):
            GeoIP2(invalid_path)