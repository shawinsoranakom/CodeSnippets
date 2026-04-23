def test03a_layers(self):
        "Testing Data Source Layers."
        for source in ds_list:
            ds = DataSource(source.ds)

            # Incrementing through each layer, this tests DataSource.__iter__
            for layer in ds:
                self.assertEqual(layer.name, source.name)
                self.assertEqual(str(layer), source.name)
                # Making sure we get the number of features we expect
                self.assertEqual(len(layer), source.nfeat)

                # Making sure we get the number of fields we expect
                self.assertEqual(source.nfld, layer.num_fields)
                self.assertEqual(source.nfld, len(layer.fields))

                # Testing the layer's extent (an Envelope), and its properties
                self.assertIsInstance(layer.extent, Envelope)
                self.assertAlmostEqual(source.extent[0], layer.extent.min_x, 5)
                self.assertAlmostEqual(source.extent[1], layer.extent.min_y, 5)
                self.assertAlmostEqual(source.extent[2], layer.extent.max_x, 5)
                self.assertAlmostEqual(source.extent[3], layer.extent.max_y, 5)

                # Now checking the field names.
                flds = layer.fields
                for f in flds:
                    self.assertIn(f, source.fields)

                # Negative FIDs are not allowed.
                with self.assertRaisesMessage(
                    IndexError, "Negative indices are not allowed on OGR Layers."
                ):
                    layer.__getitem__(-1)
                with self.assertRaisesMessage(IndexError, "Invalid feature id: 50000."):
                    layer.__getitem__(50000)

                if hasattr(source, "field_values"):
                    # Testing `Layer.get_fields` (which uses Layer.__iter__)
                    for fld_name, fld_value in source.field_values.items():
                        self.assertEqual(fld_value, layer.get_fields(fld_name))

                    # Testing `Layer.__getitem__`.
                    for i, fid in enumerate(source.fids):
                        feat = layer[fid]
                        self.assertEqual(fid, feat.fid)
                        # Maybe this should be in the test below, but we might
                        # as well test the feature values here while in this
                        # loop.
                        for fld_name, fld_value in source.field_values.items():
                            self.assertEqual(fld_value[i], feat.get(fld_name))

                        msg = (
                            "Index out of range when accessing field in a feature: %s."
                        )
                        with self.assertRaisesMessage(IndexError, msg % len(feat)):
                            feat.__getitem__(len(feat))

                        with self.assertRaisesMessage(
                            IndexError, "Invalid OFT field name given: invalid."
                        ):
                            feat.__getitem__("invalid")