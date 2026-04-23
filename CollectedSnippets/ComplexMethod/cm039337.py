def _validate_input(self, X, y, incremental, reset):
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csr", "csc"],
            multi_output=True,
            dtype=(np.float64, np.float32),
            reset=reset,
        )
        if y.ndim == 2 and y.shape[1] == 1:
            y = column_or_1d(y, warn=True)

        # Matrix of actions to be taken under the possible combinations:
        # The case that incremental == True and classes_ not defined is
        # already checked by _check_partial_fit_first_call that is called
        # in _partial_fit below.
        # The cases are already grouped into the respective if blocks below.
        #
        # incremental warm_start classes_ def  action
        #    0            0         0        define classes_
        #    0            1         0        define classes_
        #    0            0         1        redefine classes_
        #
        #    0            1         1        check compat warm_start
        #    1            1         1        check compat warm_start
        #
        #    1            0         1        check compat last fit
        #
        # Note the reliance on short-circuiting here, so that the second
        # or part implies that classes_ is defined.
        if (not hasattr(self, "classes_")) or (not self.warm_start and not incremental):
            self._label_binarizer = LabelBinarizer()
            self._label_binarizer.fit(y)
            self.classes_ = self._label_binarizer.classes_
        else:
            classes = unique_labels(y)
            if self.warm_start:
                if set(classes) != set(self.classes_):
                    raise ValueError(
                        "warm_start can only be used where `y` has the same "
                        "classes as in the previous call to fit. Previously "
                        f"got {self.classes_}, `y` has {classes}"
                    )
            elif len(np.setdiff1d(classes, self.classes_, assume_unique=True)):
                raise ValueError(
                    "`y` has classes not in `self.classes_`. "
                    f"`self.classes_` has {self.classes_}. 'y' has {classes}."
                )

        # This downcast to bool is to prevent upcasting when working with
        # float32 data
        y = self._label_binarizer.transform(y).astype(bool)
        return X, y