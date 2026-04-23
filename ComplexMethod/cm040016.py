def __init__(
        self,
        bin_boundaries=None,
        num_bins=None,
        epsilon=0.01,
        output_mode="int",
        sparse=False,
        dtype=None,
        name=None,
    ):
        super().__init__(name=name, dtype=dtype)

        if sparse and not backend.SUPPORTS_SPARSE_TENSORS:
            raise ValueError(
                f"`sparse=True` cannot be used with backend {backend.backend()}"
            )
        if sparse and output_mode == "int":
            raise ValueError(
                "`sparse=True` may only be used if `output_mode` is "
                "`'one_hot'`, `'multi_hot'`, or `'count'`. "
                f"Received: sparse={sparse} and "
                f"output_mode={output_mode}"
            )

        argument_validation.validate_string_arg(
            output_mode,
            allowable_strings=(
                "int",
                "one_hot",
                "multi_hot",
                "count",
            ),
            caller_name=self.__class__.__name__,
            arg_name="output_mode",
        )

        if num_bins is not None and num_bins < 0:
            raise ValueError(
                "`num_bins` must be greater than or equal to 0. "
                f"Received: `num_bins={num_bins}`"
            )
        if num_bins is not None and bin_boundaries is not None:
            raise ValueError(
                "Both `num_bins` and `bin_boundaries` should not be set. "
                f"Received: `num_bins={num_bins}` and "
                f"`bin_boundaries={bin_boundaries}`"
            )
        if num_bins is None and bin_boundaries is None:
            raise ValueError(
                "You need to set either `num_bins` or `bin_boundaries`."
            )

        self.bin_boundaries = bin_boundaries
        self.num_bins = num_bins
        self.epsilon = epsilon
        self.output_mode = output_mode
        self.sparse = sparse

        if self.bin_boundaries:
            self.summary = None
        else:
            self.summary = np.array([[], []], dtype="float32")