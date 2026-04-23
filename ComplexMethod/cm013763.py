def __init__(
        self,
        kernel_size: _size_2_t,
        output_size: _size_2_t | None = None,
        output_ratio: _ratio_2_t | None = None,
        return_indices: bool = False,
        _random_samples=None,
    ) -> None:
        super().__init__()
        self.kernel_size = _pair(kernel_size)
        self.return_indices = return_indices
        self.register_buffer("_random_samples", _random_samples)
        self.output_size = _pair(output_size) if output_size is not None else None
        self.output_ratio = _pair(output_ratio) if output_ratio is not None else None
        if output_size is None and output_ratio is None:
            raise ValueError(
                "FractionalMaxPool2d requires specifying either "
                "an output size, or a pooling ratio"
            )
        if output_size is not None and output_ratio is not None:
            raise ValueError(
                "only one of output_size and output_ratio may be specified"
            )
        if self.output_ratio is not None:
            if not (0 < self.output_ratio[0] < 1 and 0 < self.output_ratio[1] < 1):
                raise ValueError(
                    f"output_ratio must be between 0 and 1 (got {output_ratio})"
                )