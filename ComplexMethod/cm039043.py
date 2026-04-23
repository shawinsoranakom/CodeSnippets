def _get_kernel_params(self):
        params = self.kernel_params
        if params is None:
            params = {}
        if not callable(self.kernel) and self.kernel != "precomputed":
            for param in KERNEL_PARAMS[self.kernel]:
                if getattr(self, param) is not None:
                    params[param] = getattr(self, param)
        else:
            if (
                self.gamma is not None
                or self.coef0 is not None
                or self.degree is not None
            ):
                raise ValueError(
                    "Don't pass gamma, coef0 or degree to "
                    "Nystroem if using a callable "
                    "or precomputed kernel"
                )

        return params