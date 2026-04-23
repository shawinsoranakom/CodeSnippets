def __init__(
        self,
        featurewise_center=False,
        samplewise_center=False,
        featurewise_std_normalization=False,
        samplewise_std_normalization=False,
        zca_whitening=False,
        zca_epsilon=1e-6,
        rotation_range=0,
        width_shift_range=0.0,
        height_shift_range=0.0,
        brightness_range=None,
        shear_range=0.0,
        zoom_range=0.0,
        channel_shift_range=0.0,
        fill_mode="nearest",
        cval=0.0,
        horizontal_flip=False,
        vertical_flip=False,
        rescale=None,
        preprocessing_function=None,
        data_format=None,
        validation_split=0.0,
        interpolation_order=1,
        dtype=None,
    ):
        if data_format is None:
            data_format = backend.image_data_format()
        if dtype is None:
            dtype = backend.floatx()

        self.featurewise_center = featurewise_center
        self.samplewise_center = samplewise_center
        self.featurewise_std_normalization = featurewise_std_normalization
        self.samplewise_std_normalization = samplewise_std_normalization
        self.zca_whitening = zca_whitening
        self.zca_epsilon = zca_epsilon
        self.rotation_range = rotation_range
        self.width_shift_range = width_shift_range
        self.height_shift_range = height_shift_range
        self.shear_range = shear_range
        self.zoom_range = zoom_range
        self.channel_shift_range = channel_shift_range
        self.fill_mode = fill_mode
        self.cval = cval
        self.horizontal_flip = horizontal_flip
        self.vertical_flip = vertical_flip
        self.rescale = rescale
        self.preprocessing_function = preprocessing_function
        self.dtype = dtype
        self.interpolation_order = interpolation_order

        if data_format not in {"channels_last", "channels_first"}:
            raise ValueError(
                '`data_format` should be `"channels_last"` '
                "(channel after row and column) or "
                '`"channels_first"` (channel before row and column). '
                f"Received: {data_format}"
            )
        self.data_format = data_format
        if data_format == "channels_first":
            self.channel_axis = 1
            self.row_axis = 2
            self.col_axis = 3
        if data_format == "channels_last":
            self.channel_axis = 3
            self.row_axis = 1
            self.col_axis = 2
        if validation_split and not 0 < validation_split < 1:
            raise ValueError(
                "`validation_split` must be strictly between 0 and 1. "
                f" Received: {validation_split}"
            )
        self._validation_split = validation_split

        self.mean = None
        self.std = None
        self.zca_whitening_matrix = None

        if isinstance(zoom_range, (float, int)):
            self.zoom_range = [1 - zoom_range, 1 + zoom_range]
        elif len(zoom_range) == 2 and all(
            isinstance(val, (float, int)) for val in zoom_range
        ):
            self.zoom_range = [zoom_range[0], zoom_range[1]]
        else:
            raise ValueError(
                "`zoom_range` should be a float or "
                "a tuple or list of two floats. "
                f"Received: {zoom_range}"
            )
        if zca_whitening:
            if not featurewise_center:
                self.featurewise_center = True
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`zca_whitening`, which overrides "
                    "setting of `featurewise_center`."
                )
            if featurewise_std_normalization:
                self.featurewise_std_normalization = False
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`zca_whitening` "
                    "which overrides setting of"
                    "`featurewise_std_normalization`."
                )
        if featurewise_std_normalization:
            if not featurewise_center:
                self.featurewise_center = True
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`featurewise_std_normalization`, "
                    "which overrides setting of "
                    "`featurewise_center`."
                )
        if samplewise_std_normalization:
            if not samplewise_center:
                self.samplewise_center = True
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`samplewise_std_normalization`, "
                    "which overrides setting of "
                    "`samplewise_center`."
                )
        if brightness_range is not None:
            if (
                not isinstance(brightness_range, (tuple, list))
                or len(brightness_range) != 2
            ):
                raise ValueError(
                    "`brightness_range should be tuple or list of two floats. "
                    f"Received: {brightness_range}"
                )
        self.brightness_range = brightness_range