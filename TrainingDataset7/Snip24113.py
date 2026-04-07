def test_band_data_setters(self):
        # Create in-memory raster and get band
        rsmem = GDALRaster(
            {
                "datatype": 1,
                "driver": "MEM",
                "name": "mem_rst",
                "width": 10,
                "height": 10,
                "nr_of_bands": 1,
                "srid": 4326,
            }
        )
        bandmem = rsmem.bands[0]

        # Set nodata value
        bandmem.nodata_value = 99
        self.assertEqual(bandmem.nodata_value, 99)

        # Set data for entire dataset
        bandmem.data(range(100))
        if numpy:
            numpy.testing.assert_equal(
                bandmem.data(), numpy.arange(100).reshape(10, 10)
            )
        else:
            self.assertEqual(bandmem.data(), list(range(100)))

        # Prepare data for setting values in subsequent tests
        block = list(range(100, 104))
        packed_block = struct.pack("<" + "B B B B", *block)

        # Set data from list
        bandmem.data(block, (1, 1), (2, 2))
        result = bandmem.data(offset=(1, 1), size=(2, 2))
        if numpy:
            numpy.testing.assert_equal(result, numpy.array(block).reshape(2, 2))
        else:
            self.assertEqual(result, block)

        # Set data from packed block
        bandmem.data(packed_block, (1, 1), (2, 2))
        result = bandmem.data(offset=(1, 1), size=(2, 2))
        if numpy:
            numpy.testing.assert_equal(result, numpy.array(block).reshape(2, 2))
        else:
            self.assertEqual(result, block)

        # Set data from bytes
        bandmem.data(bytes(packed_block), (1, 1), (2, 2))
        result = bandmem.data(offset=(1, 1), size=(2, 2))
        if numpy:
            numpy.testing.assert_equal(result, numpy.array(block).reshape(2, 2))
        else:
            self.assertEqual(result, block)

        # Set data from bytearray
        bandmem.data(bytearray(packed_block), (1, 1), (2, 2))
        result = bandmem.data(offset=(1, 1), size=(2, 2))
        if numpy:
            numpy.testing.assert_equal(result, numpy.array(block).reshape(2, 2))
        else:
            self.assertEqual(result, block)

        # Set data from memoryview
        bandmem.data(memoryview(packed_block), (1, 1), (2, 2))
        result = bandmem.data(offset=(1, 1), size=(2, 2))
        if numpy:
            numpy.testing.assert_equal(result, numpy.array(block).reshape(2, 2))
        else:
            self.assertEqual(result, block)

        # Set data from numpy array
        if numpy:
            bandmem.data(numpy.array(block, dtype="int8").reshape(2, 2), (1, 1), (2, 2))
            numpy.testing.assert_equal(
                bandmem.data(offset=(1, 1), size=(2, 2)),
                numpy.array(block).reshape(2, 2),
            )

        # Test json input data
        rsmemjson = GDALRaster(JSON_RASTER)
        bandmemjson = rsmemjson.bands[0]
        if numpy:
            numpy.testing.assert_equal(
                bandmemjson.data(), numpy.array(range(25)).reshape(5, 5)
            )
        else:
            self.assertEqual(bandmemjson.data(), list(range(25)))