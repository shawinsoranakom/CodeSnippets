def test_band_data_replication(self):
        band = GDALRaster(
            {
                "srid": 4326,
                "width": 3,
                "height": 3,
                "bands": [{"data": range(10, 19), "nodata_value": 0}],
            }
        ).bands[0]

        # Variations for input (data, shape, expected result).
        combos = (
            ([1], (1, 1), [1] * 9),
            (range(3), (1, 3), [0, 0, 0, 1, 1, 1, 2, 2, 2]),
            (range(3), (3, 1), [0, 1, 2, 0, 1, 2, 0, 1, 2]),
        )
        for combo in combos:
            band.data(combo[0], shape=combo[1])
            if numpy:
                numpy.testing.assert_equal(
                    band.data(), numpy.array(combo[2]).reshape(3, 3)
                )
            else:
                self.assertEqual(band.data(), list(combo[2]))