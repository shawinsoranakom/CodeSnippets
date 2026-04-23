def __init__(
        self,
        dataframe,
        directory=None,
        image_data_generator=None,
        x_col="filename",
        y_col="class",
        weight_col=None,
        target_size=(256, 256),
        color_mode="rgb",
        classes=None,
        class_mode="categorical",
        batch_size=32,
        shuffle=True,
        seed=None,
        data_format="channels_last",
        save_to_dir=None,
        save_prefix="",
        save_format="png",
        subset=None,
        interpolation="nearest",
        keep_aspect_ratio=False,
        dtype="float32",
        validate_filenames=True,
    ):
        super().set_processing_attrs(
            image_data_generator,
            target_size,
            color_mode,
            data_format,
            save_to_dir,
            save_prefix,
            save_format,
            subset,
            interpolation,
            keep_aspect_ratio,
        )
        df = dataframe.copy()
        self.directory = directory or ""
        self.class_mode = class_mode
        self.dtype = dtype
        # check that inputs match the required class_mode
        self._check_params(df, x_col, y_col, weight_col, classes)
        if (
            validate_filenames
        ):  # check which image files are valid and keep them
            df = self._filter_valid_filepaths(df, x_col)
        if class_mode not in ["input", "multi_output", "raw", None]:
            df, classes = self._filter_classes(df, y_col, classes)
            num_classes = len(classes)
            # build an index of all the unique classes
            self.class_indices = dict(zip(classes, range(len(classes))))
        # retrieve only training or validation set
        if self.split:
            num_files = len(df)
            start = int(self.split[0] * num_files)
            stop = int(self.split[1] * num_files)
            df = df.iloc[start:stop, :]
        # get labels for each observation
        if class_mode not in ["input", "multi_output", "raw", None]:
            self.classes = self.get_classes(df, y_col)
        self.filenames = df[x_col].tolist()
        self._sample_weight = df[weight_col].values if weight_col else None

        if class_mode == "multi_output":
            self._targets = [np.array(df[col].tolist()) for col in y_col]
        if class_mode == "raw":
            self._targets = df[y_col].values
        self.samples = len(self.filenames)
        validated_string = (
            "validated" if validate_filenames else "non-validated"
        )
        if class_mode in ["input", "multi_output", "raw", None]:
            io_utils.print_msg(
                f"Found {self.samples} {validated_string} image filenames."
            )
        else:
            io_utils.print_msg(
                f"Found {self.samples} {validated_string} image filenames "
                f"belonging to {num_classes} classes."
            )
        self._filepaths = [
            os.path.join(self.directory, fname) for fname in self.filenames
        ]
        super().__init__(self.samples, batch_size, shuffle, seed)