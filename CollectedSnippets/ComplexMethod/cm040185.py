def _check_params(self, df, x_col, y_col, weight_col, classes):
        # check class mode is one of the currently supported
        if self.class_mode not in self.allowed_class_modes:
            raise ValueError(
                "Invalid class_mode: {}; expected one of: {}".format(
                    self.class_mode, self.allowed_class_modes
                )
            )
        # check that y_col has several column names if class_mode is
        # multi_output
        if (self.class_mode == "multi_output") and not isinstance(y_col, list):
            raise TypeError(
                'If class_mode="{}", y_col must be a list. Received {}.'.format(
                    self.class_mode, type(y_col).__name__
                )
            )
        # check that filenames/filepaths column values are all strings
        if not all(df[x_col].apply(lambda x: isinstance(x, str))):
            raise TypeError(
                f"All values in column x_col={x_col} must be strings."
            )
        # check labels are string if class_mode is binary or sparse
        if self.class_mode in {"binary", "sparse"}:
            if not all(df[y_col].apply(lambda x: isinstance(x, str))):
                raise TypeError(
                    'If class_mode="{}", y_col="{}" column '
                    "values must be strings.".format(self.class_mode, y_col)
                )
        # check that if binary there are only 2 different classes
        if self.class_mode == "binary":
            if classes:
                classes = set(classes)
                if len(classes) != 2:
                    raise ValueError(
                        'If class_mode="binary" there must be 2 '
                        "classes. {} class/es were given.".format(len(classes))
                    )
            elif df[y_col].nunique() != 2:
                raise ValueError(
                    'If class_mode="binary" there must be 2 classes. '
                    "Found {} classes.".format(df[y_col].nunique())
                )
        # check values are string, list or tuple if class_mode is categorical
        if self.class_mode == "categorical":
            types = (str, list, tuple)
            if not all(df[y_col].apply(lambda x: isinstance(x, types))):
                raise TypeError(
                    'If class_mode="{}", y_col="{}" column '
                    "values must be type string, list or tuple.".format(
                        self.class_mode, y_col
                    )
                )
        # raise warning if classes are given but will be unused
        if classes and self.class_mode in {
            "input",
            "multi_output",
            "raw",
            None,
        }:
            warnings.warn(
                '`classes` will be ignored given the class_mode="{}"'.format(
                    self.class_mode
                )
            )
        # check that if weight column that the values are numerical
        if weight_col and not issubclass(df[weight_col].dtype.type, np.number):
            raise TypeError(f"Column weight_col={weight_col} must be numeric.")