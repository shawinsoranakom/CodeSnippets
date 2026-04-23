def test04_features(self):
        "Testing Data Source Features."
        for source in ds_list:
            ds = DataSource(source.ds)

            # Incrementing through each layer
            for layer in ds:
                # Incrementing through each feature in the layer
                for feat in layer:
                    # Making sure the number of fields, and the geometry type
                    # are what's expected.
                    self.assertEqual(source.nfld, len(list(feat)))
                    self.assertEqual(source.gtype, feat.geom_type)

                    # Making sure the fields match to an appropriate OFT type.
                    for k, v in source.fields.items():
                        # Making sure we get the proper OGR Field instance,
                        # using a string value index for the feature.
                        self.assertIsInstance(feat[k], v)
                    self.assertIsInstance(feat.fields[0], str)

                    # Testing Feature.__iter__
                    for fld in feat:
                        self.assertIn(fld.name, source.fields)