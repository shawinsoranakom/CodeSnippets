def standardize(self, x):
        """Applies the normalization configuration in-place to a batch of
        inputs.

        `x` is changed in-place since the function is mainly used internally
        to standardize images and feed them to your network. If a copy of `x`
        would be created instead it would have a significant performance cost.
        If you want to apply this method without changing the input in-place
        you can call the method creating a copy before:

        standardize(np.copy(x))

        Args:
            x: Batch of inputs to be normalized.

        Returns:
            The inputs, normalized.
        """
        if self.preprocessing_function:
            x = self.preprocessing_function(x)
        if self.rescale:
            x *= self.rescale
        if self.samplewise_center:
            x -= np.mean(x, keepdims=True)
        if self.samplewise_std_normalization:
            x /= np.std(x, keepdims=True) + 1e-6

        if self.featurewise_center:
            if self.mean is not None:
                x -= self.mean
            else:
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`featurewise_center`, but it hasn't "
                    "been fit on any training data. Fit it "
                    "first by calling `.fit(numpy_data)`."
                )
        if self.featurewise_std_normalization:
            if self.std is not None:
                x /= self.std + 1e-6
            else:
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`featurewise_std_normalization`, "
                    "but it hasn't "
                    "been fit on any training data. Fit it "
                    "first by calling `.fit(numpy_data)`."
                )
        if self.zca_whitening:
            if self.zca_whitening_matrix is not None:
                flat_x = x.reshape(-1, np.prod(x.shape[-3:]))
                white_x = flat_x @ self.zca_whitening_matrix
                x = np.reshape(white_x, x.shape)
            else:
                warnings.warn(
                    "This ImageDataGenerator specifies "
                    "`zca_whitening`, but it hasn't "
                    "been fit on any training data. Fit it "
                    "first by calling `.fit(numpy_data)`."
                )
        return x