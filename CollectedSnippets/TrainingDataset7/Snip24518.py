def test_layermap_strict(self):
        "Testing the `strict` keyword, and import of a LineString shapefile."
        # When the `strict` keyword is set an error encountered will force
        # the importation to stop.
        with self.assertRaises(InvalidDecimal):
            lm = LayerMapping(Interstate, inter_shp, inter_mapping)
            lm.save(silent=True, strict=True)
        Interstate.objects.all().delete()

        # This LayerMapping should work b/c `strict` is not set.
        lm = LayerMapping(Interstate, inter_shp, inter_mapping)
        lm.save(silent=True)

        # Two interstate should have imported correctly.
        self.assertEqual(2, Interstate.objects.count())

        # Verifying the values in the layer w/the model.
        ds = DataSource(inter_shp)

        # Only the first two features of this shapefile are valid.
        valid_feats = ds[0][:2]
        for feat in valid_feats:
            istate = Interstate.objects.get(name=feat["Name"].value)

            if feat.fid == 0:
                self.assertEqual(Decimal(str(feat["Length"])), istate.length)
            elif feat.fid == 1:
                # Everything but the first two decimal digits were truncated,
                # because the Interstate model's `length` field has
                # decimal_places=2.
                self.assertAlmostEqual(feat.get("Length"), float(istate.length), 2)

            for p1, p2 in zip(feat.geom, istate.path):
                self.assertAlmostEqual(p1[0], p2[0], 6)
                self.assertAlmostEqual(p1[1], p2[1], 6)