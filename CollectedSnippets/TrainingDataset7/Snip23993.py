def test_ds_input_pathlib(self):
        test_shp = Path(get_ds_file("test_point", "shp"))
        ds = DataSource(test_shp)
        self.assertEqual(len(ds), 1)