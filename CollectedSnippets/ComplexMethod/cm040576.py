def test_affine_transform(self, interpolation, fill_mode):
        if backend.backend() == "tensorflow" and fill_mode == "mirror":
            self.skipTest(
                "In tensorflow backend, applying affine_transform with "
                "fill_mode=mirror is not supported"
            )
        if backend.backend() == "tensorflow" and fill_mode == "wrap":
            self.skipTest(
                "In tensorflow backend, the numerical results of applying "
                "affine_transform with fill_mode=wrap is inconsistent with"
                "scipy"
            )
        if (
            testing.jax_uses_tpu()
            and interpolation == "bilinear"
            and fill_mode == "constant"
        ):
            self.skipTest(
                "JAX on TPU interpolation='bilinear' and fill_mode='constant' "
                "Produces one incorrect pixel in the corner"
            )

        # TODO: `nearest` interpolation in jax and torch causes random index
        # shifting, resulting in significant differences in output which leads
        # to failure
        if backend.backend() in ("jax", "torch") and interpolation == "nearest":
            self.skipTest(
                f"In {backend.backend()} backend, "
                f"interpolation={interpolation} causes index shifting and "
                "leads test failure"
            )

        # Test channels_last
        np.random.seed(42)
        x = np.random.uniform(size=(50, 50, 3)).astype("float32") * 255
        transform = np.random.uniform(size=(6)).astype("float32")
        transform = np.pad(transform, (0, 2))  # makes c0, c1 always 0
        out = kimage.affine_transform(
            x, transform, interpolation=interpolation, fill_mode=fill_mode
        )
        coordinates = _compute_affine_transform_coordinates(x, transform)
        ref_out = _fixed_map_coordinates(
            x,
            coordinates,
            order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
            fill_mode=fill_mode,
        )
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-2, tpu_atol=10, tpu_rtol=10)

        x = np.random.uniform(size=(2, 50, 50, 3)).astype("float32") * 255
        transform = np.random.uniform(size=(2, 6)).astype("float32")
        transform = np.pad(transform, [(0, 0), (0, 2)])  # makes c0, c1 always 0
        out = kimage.affine_transform(
            x,
            transform,
            interpolation=interpolation,
            fill_mode=fill_mode,
        )
        coordinates = _compute_affine_transform_coordinates(x, transform)
        ref_out = np.stack(
            [
                _fixed_map_coordinates(
                    x[i],
                    coordinates[i],
                    order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                    fill_mode=fill_mode,
                )
                for i in range(x.shape[0])
            ],
            axis=0,
        )
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-2, tpu_atol=10, tpu_rtol=10)

        # Test channels_first
        backend.set_image_data_format("channels_first")
        x = np.random.uniform(size=(3, 50, 50)).astype("float32") * 255
        transform = np.random.uniform(size=(6)).astype("float32")
        transform = np.pad(transform, (0, 2))  # makes c0, c1 always 0
        out = kimage.affine_transform(
            x, transform, interpolation=interpolation, fill_mode=fill_mode
        )
        coordinates = _compute_affine_transform_coordinates(
            np.transpose(x, [1, 2, 0]), transform
        )
        ref_out = _fixed_map_coordinates(
            np.transpose(x, [1, 2, 0]),
            coordinates,
            order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
            fill_mode=fill_mode,
        )
        ref_out = np.transpose(ref_out, [2, 0, 1])
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-2, tpu_atol=1, tpu_rtol=1)

        x = np.random.uniform(size=(2, 3, 50, 50)).astype("float32") * 255
        transform = np.random.uniform(size=(2, 6)).astype("float32")
        transform = np.pad(transform, [(0, 0), (0, 2)])  # makes c0, c1 always 0
        out = kimage.affine_transform(
            x,
            transform,
            interpolation=interpolation,
            fill_mode=fill_mode,
        )
        coordinates = _compute_affine_transform_coordinates(
            np.transpose(x, [0, 2, 3, 1]), transform
        )
        ref_out = np.stack(
            [
                _fixed_map_coordinates(
                    np.transpose(x[i], [1, 2, 0]),
                    coordinates[i],
                    order=AFFINE_TRANSFORM_INTERPOLATIONS[interpolation],
                    fill_mode=fill_mode,
                )
                for i in range(x.shape[0])
            ],
            axis=0,
        )
        ref_out = np.transpose(ref_out, [0, 3, 1, 2])
        self.assertEqual(tuple(out.shape), tuple(ref_out.shape))
        self.assertAllClose(out, ref_out, atol=1e-2, tpu_atol=10, tpu_rtol=10)

        # Test class
        out = kimage.AffineTransform(
            interpolation=interpolation, fill_mode=fill_mode
        )(x, transform)
        self.assertAllClose(out, ref_out, atol=1e-2, tpu_atol=10, tpu_rtol=10)