def test_zero_padding_3d(self, data_format):
        inputs = np.random.rand(1, 2, 3, 4, 5)
        outputs = layers.ZeroPadding3D(
            padding=((1, 2), (3, 4), (0, 2)), data_format=data_format
        )(inputs)

        if data_format == "channels_first":
            for index in [0, -1, -2]:
                self.assertAllClose(outputs[:, :, index, :, :], 0.0)
            for index in [0, 1, 2, -1, -2, -3, -4]:
                self.assertAllClose(outputs[:, :, :, index, :], 0.0)
            for index in [-1, -2]:
                self.assertAllClose(outputs[:, :, :, :, index], 0.0)
            self.assertAllClose(outputs[:, :, 1:-2, 3:-4, 0:-2], inputs)
        else:
            for index in [0, -1, -2]:
                self.assertAllClose(outputs[:, index, :, :, :], 0.0)
            for index in [0, 1, 2, -1, -2, -3, -4]:
                self.assertAllClose(outputs[:, :, index, :, :], 0.0)
            for index in [-1, -2]:
                self.assertAllClose(outputs[:, :, :, index, :], 0.0)
            self.assertAllClose(outputs[:, 1:-2, 3:-4, 0:-2, :], inputs)