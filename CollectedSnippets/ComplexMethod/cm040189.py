def fit(self, x, augment=False, rounds=1, seed=None):
        """Fits the data generator to some sample data.

        This computes the internal data stats related to the
        data-dependent transformations, based on an array of sample data.

        Only required if `featurewise_center` or
        `featurewise_std_normalization` or `zca_whitening`
        are set to `True`.

        When `rescale` is set to a value, rescaling is applied to
        sample data before computing the internal data stats.

        Args:
            x: Sample data. Should have rank 4.
             In case of grayscale data,
             the channels axis should have value 1, in case
             of RGB data, it should have value 3, and in case
             of RGBA data, it should have value 4.
            augment: Boolean (default: False).
                Whether to fit on randomly augmented samples.
            rounds: Int (default: 1).
                If using data augmentation (`augment=True`),
                this is how many augmentation passes over the data to use.
            seed: Int (default: None). Random seed.
        """
        x = np.asarray(x, dtype=self.dtype)
        if x.ndim != 4:
            raise ValueError(
                "Input to `.fit()` should have rank 4. Got array with shape: "
                + str(x.shape)
            )
        if x.shape[self.channel_axis] not in {1, 3, 4}:
            warnings.warn(
                "Expected input to be images (as Numpy array) "
                f'following the data format convention "{self.data_format}'
                f'" (channels on axis {self.channel_axis})'
                ", i.e. expected either 1, 3 or 4 channels on axis "
                f"{self.channel_axis}. However, it was passed an array with"
                f" shape {x.shape} ({x.shape[self.channel_axis]} channels)."
            )

        if seed is not None:
            np.random.seed(seed)

        x = np.copy(x)
        if self.rescale:
            x *= self.rescale

        if augment:
            ax = np.zeros(
                tuple([rounds * x.shape[0]] + list(x.shape)[1:]),
                dtype=self.dtype,
            )
            for r in range(rounds):
                for i in range(x.shape[0]):
                    ax[i + r * x.shape[0]] = self.random_transform(x[i])
            x = ax

        if self.featurewise_center:
            self.mean = np.mean(x, axis=(0, self.row_axis, self.col_axis))
            broadcast_shape = [1, 1, 1]
            broadcast_shape[self.channel_axis - 1] = x.shape[self.channel_axis]
            self.mean = np.reshape(self.mean, broadcast_shape)
            x -= self.mean

        if self.featurewise_std_normalization:
            self.std = np.std(x, axis=(0, self.row_axis, self.col_axis))
            broadcast_shape = [1, 1, 1]
            broadcast_shape[self.channel_axis - 1] = x.shape[self.channel_axis]
            self.std = np.reshape(self.std, broadcast_shape)
            x /= self.std + 1e-6

        if self.zca_whitening:
            n = len(x)
            flat_x = np.reshape(x, (n, -1))

            u, s, _ = np.linalg.svd(flat_x.T, full_matrices=False)
            s_inv = np.sqrt(n) / (s + self.zca_epsilon)
            self.zca_whitening_matrix = (u * s_inv).dot(u.T)