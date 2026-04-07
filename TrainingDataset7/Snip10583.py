def _get_repr_options(self):
        return {**super()._get_repr_options(), "sample": self.function == "STDDEV_SAMP"}