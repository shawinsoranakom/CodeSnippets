def test_nonexistent_field(self):
        source = ds_list[0]
        ds = DataSource(source.ds)
        msg = "invalid field name: nonexistent"
        with self.assertRaisesMessage(GDALException, msg):
            ds[0].get_fields("nonexistent")