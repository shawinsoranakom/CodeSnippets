def test03b_layer_slice(self):
        "Test indexing and slicing on Layers."
        # Using the first data-source because the same slice
        # can be used for both the layer and the control values.
        source = ds_list[0]
        ds = DataSource(source.ds)

        sl = slice(1, 3)
        feats = ds[0][sl]

        for fld_name in ds[0].fields:
            test_vals = [feat.get(fld_name) for feat in feats]
            control_vals = source.field_values[fld_name][sl]
            self.assertEqual(control_vals, test_vals)