def __init__(
        self,
        dtype=None,
        shape=None,
        ndim=None,
        max_ndim=None,
        min_ndim=None,
        axes=None,
        allow_last_axis_squeeze=False,
        name=None,
        optional=False,
    ):
        self.dtype = (
            backend.standardize_dtype(dtype) if dtype is not None else None
        )
        if shape is not None:
            self.shape = backend.standardize_shape(shape)
            self.ndim = len(shape)
        else:
            self.ndim = ndim
            self.shape = None
        self.max_ndim = max_ndim
        self.min_ndim = min_ndim
        self.name = name
        self.optional = optional
        self.allow_last_axis_squeeze = allow_last_axis_squeeze
        try:
            axes = axes or {}
            self.axes = {int(k): axes[k] for k in axes}
        except (ValueError, TypeError):
            raise TypeError(
                "Argument `axes` must be a dict with integer keys. "
                f"Received: axes={axes}"
            )

        if self.axes and (self.ndim is not None or self.max_ndim is not None):
            max_dim = (self.ndim if self.ndim else self.max_ndim) - 1
            max_axis = max(self.axes)
            if max_axis > max_dim:
                raise ValueError(
                    "Axis {} is greater than the maximum "
                    "allowed value: {}".format(max_axis, max_dim)
                )