def __post_init__(self):
        (
            foreach_method,
            foreach_method_inplace,
            torch_ref_method,
            torch_ref_inplace,
        ) = get_foreach_method_names(self.name)
        if not self.supports_out:
            # note(crcrpar): `foreach_method` for `"zero"` is `None` but `None` would call
            # `_getattr_qual` in `OpInfo.__post_init__` which should fail since `_foreach_zero`
            # is not defined at the moment. Thus to skip the qualification, set a similar torch
            # function.
            if foreach_method is not None:
                raise AssertionError("foreach_method must be None")
            if torch_ref_method is not None:
                raise AssertionError("torch_ref_method must be None")
            foreach_method = foreach_method_inplace
            torch_ref_method = torch_ref_inplace

        # We disable all complex128 tests internally for foreach due to reported flakiness
        # tracked in #139648
        supported_dtypes = get_all_dtypes(include_qint=False)
        if IS_FBCODE:
            supported_dtypes = [
                x for x in supported_dtypes if x is not torch.complex128
            ]
        self.dtypes = _dispatch_dtypes(supported_dtypes)

        self.op = foreach_method
        self.method_variant = foreach_method
        self.ref = torch_ref_method
        self.inplace_variant = foreach_method_inplace
        self.ref_inplace = torch_ref_inplace
        self.has_no_in_place = self.inplace_variant is None

        name = self.name
        self.name = f"_foreach_{name}"
        if name == "norm":
            self.ref = torch.linalg.vector_norm
        elif name == "minimum":
            # because minimum ref does not support inplace or scalar
            self.ref = torch.clamp_max
            self.ref_inplace = torch.Tensor.clamp_max_
        elif name == "maximum":
            # because maximum ref does not support inplace or scalar
            self.ref = torch.clamp_min
            self.ref_inplace = torch.Tensor.clamp_min_

        # The following sets `dtypesIfCUDA` and `dtypesIfROCM` accordingly.
        super().__post_init__()