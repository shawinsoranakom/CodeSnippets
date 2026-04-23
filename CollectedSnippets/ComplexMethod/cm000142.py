def __init__(
        self,
        images,
        labels,
        fake_data=False,
        one_hot=False,
        dtype=dtypes.float32,
        reshape=True,
        seed=None,
    ):
        """Construct a _DataSet.

        one_hot arg is used only if fake_data is true.  `dtype` can be either
        `uint8` to leave the input as `[0, 255]`, or `float32` to rescale into
        `[0, 1]`.  Seed arg provides for convenient deterministic testing.

        Args:
          images: The images
          labels: The labels
          fake_data: Ignore inages and labels, use fake data.
          one_hot: Bool, return the labels as one hot vectors (if True) or ints (if
            False).
          dtype: Output image dtype. One of [uint8, float32]. `uint8` output has
            range [0,255]. float32 output has range [0,1].
          reshape: Bool. If True returned images are returned flattened to vectors.
          seed: The random seed to use.
        """
        seed1, seed2 = random_seed.get_seed(seed)
        # If op level seed is not set, use whatever graph level seed is returned
        self._rng = np.random.default_rng(seed1 if seed is None else seed2)
        dtype = dtypes.as_dtype(dtype).base_dtype
        if dtype not in (dtypes.uint8, dtypes.float32):
            msg = f"Invalid image dtype {dtype!r}, expected uint8 or float32"
            raise TypeError(msg)
        if fake_data:
            self._num_examples = 10000
            self.one_hot = one_hot
        else:
            assert images.shape[0] == labels.shape[0], (
                f"images.shape: {images.shape} labels.shape: {labels.shape}"
            )
            self._num_examples = images.shape[0]

            # Convert shape from [num examples, rows, columns, depth]
            # to [num examples, rows*columns] (assuming depth == 1)
            if reshape:
                assert images.shape[3] == 1
                images = images.reshape(
                    images.shape[0], images.shape[1] * images.shape[2]
                )
            if dtype == dtypes.float32:
                # Convert from [0, 255] -> [0.0, 1.0].
                images = images.astype(np.float32)
                images = np.multiply(images, 1.0 / 255.0)
        self._images = images
        self._labels = labels
        self._epochs_completed = 0
        self._index_in_epoch = 0