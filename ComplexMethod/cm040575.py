def test_resize(self, interpolation, antialias):
        if backend.backend() == "torch":
            if "lanczos" in interpolation:
                self.skipTest(
                    "Resizing with Lanczos interpolation is "
                    "not supported by the PyTorch backend. "
                    f"Received: interpolation={interpolation}."
                )
            if interpolation == "bicubic" and antialias is False:
                self.skipTest(
                    "Resizing with Bicubic interpolation in "
                    "PyTorch backend produces noise. Please "
                    "turn on anti-aliasing. "
                    f"Received: interpolation={interpolation}, "
                    f"antialias={antialias}."
                )
        elif backend.backend() == "openvino":
            if "lanczos" in interpolation:
                self.skipTest(
                    "Resizing with Lanczos interpolation is "
                    "not supported by the OpenVINO backend. "
                    f"Received: interpolation={interpolation}."
                )
            if interpolation == "bicubic":
                self.skipTest(
                    "Resizing with Bicubic interpolation does not match "
                    "TensorFlow strict numeric parity in the OpenVINO "
                    "backend, so this parity test is skipped. "
                    f"Received: interpolation={interpolation}."
                )
        # Test channels_last
        x = np.random.random((30, 30, 3)).astype("float32") * 255
        out = kimage.resize(
            x,
            size=(15, 15),
            interpolation=interpolation,
            antialias=antialias,
        )
        ref_out = tf.image.resize(
            x,
            size=(15, 15),
            method=interpolation,
            antialias=antialias,
        )
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-4)

        x = np.random.random((2, 30, 30, 3)).astype("float32") * 255
        out = kimage.resize(
            x,
            size=(15, 15),
            interpolation=interpolation,
            antialias=antialias,
        )
        ref_out = tf.image.resize(
            x,
            size=(15, 15),
            method=interpolation,
            antialias=antialias,
        )
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-4)

        # Test channels_first
        backend.set_image_data_format("channels_first")
        x = np.random.random((3, 30, 30)).astype("float32") * 255
        out = kimage.resize(
            x,
            size=(15, 15),
            interpolation=interpolation,
            antialias=antialias,
        )
        ref_out = tf.image.resize(
            np.transpose(x, [1, 2, 0]),
            size=(15, 15),
            method=interpolation,
            antialias=antialias,
        )
        ref_out = tf.transpose(ref_out, [2, 0, 1])
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-4)

        x = np.random.random((2, 3, 30, 30)).astype("float32") * 255
        out = kimage.resize(
            x,
            size=(15, 15),
            interpolation=interpolation,
            antialias=antialias,
        )
        ref_out = tf.image.resize(
            np.transpose(x, [0, 2, 3, 1]),
            size=(15, 15),
            method=interpolation,
            antialias=antialias,
        )
        ref_out = tf.transpose(ref_out, [0, 3, 1, 2])
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-4)

        # Test class
        out = kimage.Resize(
            size=(15, 15),
            interpolation=interpolation,
            antialias=antialias,
        )(x)
        self.assertAllClose(out, ref_out, atol=1e-4)