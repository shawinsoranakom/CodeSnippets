def test01_valid_shp(self):
        "Testing valid SHP Data Source files."

        for source in ds_list:
            # Loading up the data source
            ds = DataSource(source.ds)

            # The layer count is what's expected (only 1 layer in a SHP file).
            self.assertEqual(1, len(ds))

            # Making sure GetName works
            self.assertEqual(source.ds, ds.name)

            # Making sure the driver name matches up
            self.assertEqual(source.driver, str(ds.driver))

            # Making sure indexing works
            msg = "Index out of range when accessing layers in a datasource: %s."
            with self.assertRaisesMessage(IndexError, msg % len(ds)):
                ds.__getitem__(len(ds))

            with self.assertRaisesMessage(
                IndexError, "Invalid OGR layer name given: invalid."
            ):
                ds.__getitem__("invalid")