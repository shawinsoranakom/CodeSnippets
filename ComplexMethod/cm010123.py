def _tensor_str(self, indent):
    if self.numel() == 0:
        return "[]"

    if self.has_names():
        # There are two main codepaths (possibly more) that tensor printing goes through:
        # - tensor data can fit comfortably on screen
        # - tensor data needs to be summarized
        # Some of the codepaths don't fully support named tensors, so we send in
        # an unnamed tensor to the formatting code as a workaround.
        self = self.rename(None)

    summarize = self.numel() > PRINT_OPTS.threshold

    if self._is_zerotensor():
        self = self.clone()

    # handle the negative bit
    if self.is_neg():
        self = self.resolve_neg()

    # TODO: Remove me when `masked_select` is implemented for FP8
    if self.dtype in [
        torch.float8_e5m2,
        torch.float8_e5m2fnuz,
        torch.float8_e4m3fn,
        torch.float8_e4m3fnuz,
    ]:
        self = self.half()

    if self.dtype.is_complex:
        # handle the conjugate bit
        self = self.resolve_conj()
        real_formatter = _Formatter(
            get_summarized_data(self.real) if summarize else self.real
        )
        imag_formatter = _Formatter(
            get_summarized_data(self.imag) if summarize else self.imag
        )
        return _tensor_str_with_formatter(
            self, indent, summarize, real_formatter, imag_formatter
        )
    else:
        formatter = _Formatter(get_summarized_data(self) if summarize else self)
        return _tensor_str_with_formatter(self, indent, summarize, formatter)