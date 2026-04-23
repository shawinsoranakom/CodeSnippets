def rsample(
        self, sample_shape: _size = torch.Size(), max_try_correction=None
    ) -> Tensor:
        r"""
        .. warning::
            In some cases, sampling algorithm based on Bartlett decomposition may return singular matrix samples.
            Several tries to correct singular samples are performed by default, but it may end up returning
            singular matrix samples. Singular samples may return `-inf` values in `.log_prob()`.
            In those cases, the user should validate the samples and either fix the value of `df`
            or adjust `max_try_correction` value for argument in `.rsample` accordingly.
        """

        if max_try_correction is None:
            max_try_correction = 3 if torch._C._get_tracing_state() else 10

        sample_shape = torch.Size(sample_shape)
        sample = self._bartlett_sampling(sample_shape)

        # Below part is to improve numerical stability temporally and should be removed in the future
        is_singular = self.support.check(sample)
        if self._batch_shape:
            is_singular = is_singular.amax(self._batch_dims)

        if torch._C._get_tracing_state():
            # Less optimized version for JIT
            for _ in range(max_try_correction):
                sample_new = self._bartlett_sampling(sample_shape)
                sample = torch.where(is_singular, sample_new, sample)

                is_singular = ~self.support.check(sample)
                if self._batch_shape:
                    is_singular = is_singular.amax(self._batch_dims)

        else:
            # More optimized version with data-dependent control flow.
            if is_singular.any():
                warnings.warn("Singular sample detected.", stacklevel=2)

                for _ in range(max_try_correction):
                    sample_new = self._bartlett_sampling(is_singular[is_singular].shape)
                    sample[is_singular] = sample_new

                    is_singular_new = ~self.support.check(sample_new)
                    if self._batch_shape:
                        is_singular_new = is_singular_new.amax(self._batch_dims)
                    is_singular[is_singular.clone()] = is_singular_new

                    if not is_singular.any():
                        break

        return sample