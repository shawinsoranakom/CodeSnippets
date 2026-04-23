def __init__(
        self,
        x,
        y,
        image_data_generator,
        batch_size=32,
        shuffle=False,
        sample_weight=None,
        seed=None,
        data_format=None,
        save_to_dir=None,
        save_prefix="",
        save_format="png",
        subset=None,
        ignore_class_split=False,
        dtype=None,
    ):
        if data_format is None:
            data_format = backend.image_data_format()
        if dtype is None:
            dtype = backend.floatx()
        self.dtype = dtype
        if isinstance(x, tuple) or isinstance(x, list):
            if not isinstance(x[1], list):
                x_misc = [np.asarray(x[1])]
            else:
                x_misc = [np.asarray(xx) for xx in x[1]]
            x = x[0]
            for xx in x_misc:
                if len(x) != len(xx):
                    raise ValueError(
                        "All of the arrays in `x` "
                        "should have the same length. "
                        "Found a pair with: "
                        f"len(x[0]) = {len(x)}, len(x[?]) = {len(xx)}"
                    )
        else:
            x_misc = []

        if y is not None and len(x) != len(y):
            raise ValueError(
                "`x` (images tensor) and `y` (labels) "
                "should have the same length. "
                f"Found: x.shape = {np.asarray(x).shape}, "
                f"y.shape = {np.asarray(y).shape}"
            )
        if sample_weight is not None and len(x) != len(sample_weight):
            raise ValueError(
                "`x` (images tensor) and `sample_weight` "
                "should have the same length. "
                f"Found: x.shape = {np.asarray(x).shape}, "
                f"sample_weight.shape = {np.asarray(sample_weight).shape}"
            )
        if subset is not None:
            if subset not in {"training", "validation"}:
                raise ValueError(
                    f"Invalid subset name: {subset}"
                    '; expected "training" or "validation".'
                )
            split_idx = int(len(x) * image_data_generator._validation_split)

            if (
                y is not None
                and not ignore_class_split
                and not np.array_equal(
                    np.unique(y[:split_idx]), np.unique(y[split_idx:])
                )
            ):
                raise ValueError(
                    "Training and validation subsets "
                    "have different number of classes after "
                    "the split. If your numpy arrays are "
                    "sorted by the label, you might want "
                    "to shuffle them."
                )

            if subset == "validation":
                x = x[:split_idx]
                x_misc = [np.asarray(xx[:split_idx]) for xx in x_misc]
                if y is not None:
                    y = y[:split_idx]
            else:
                x = x[split_idx:]
                x_misc = [np.asarray(xx[split_idx:]) for xx in x_misc]
                if y is not None:
                    y = y[split_idx:]

        self.x = np.asarray(x, dtype=self.dtype)
        self.x_misc = x_misc
        if self.x.ndim != 4:
            raise ValueError(
                "Input data in `NumpyArrayIterator` "
                "should have rank 4. You passed an array "
                f"with shape {self.x.shape}"
            )
        channels_axis = 3 if data_format == "channels_last" else 1
        if self.x.shape[channels_axis] not in {1, 3, 4}:
            warnings.warn(
                f"NumpyArrayIterator is set to use the data format convention"
                f' "{data_format}" (channels on axis {channels_axis})'
                ", i.e. expected either 1, 3, or 4 channels "
                f"on axis {channels_axis}. "
                f"However, it was passed an array with shape {self.x.shape}"
                f" ({self.x.shape[channels_axis]} channels)."
            )
        if y is not None:
            self.y = np.asarray(y)
        else:
            self.y = None
        if sample_weight is not None:
            self.sample_weight = np.asarray(sample_weight)
        else:
            self.sample_weight = None
        self.image_data_generator = image_data_generator
        self.data_format = data_format
        self.save_to_dir = save_to_dir
        self.save_prefix = save_prefix
        self.save_format = save_format
        super().__init__(x.shape[0], batch_size, shuffle, seed)