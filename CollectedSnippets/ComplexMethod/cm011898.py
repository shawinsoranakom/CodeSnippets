def _default(self, name: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        out_dtype = getattr(self.dtype_prop, name)(*args, **kwargs)
        out = DTypeContainer(out_dtype, is_scalar=(name == "constant"))
        if name == "constant":
            return DTypeContainer(torch.float, is_scalar=True)

        uses_low_prec = any(
            isinstance(dtype_cont, DTypeContainer)
            and dtype_cont.dtype is not None
            and low_prec_float(dtype_cont.dtype)
            for dtype_cont in itertools.chain((out,), args, kwargs.values())
        )

        if uses_low_prec and name not in self.non_numeric_ops:
            self.low_precision_numeric_op = True

        if (
            self.disallow_fp32_ops
            and out.dtype in (torch.float32, torch.float64)
            and not out.is_scalar
        ):
            self.low_precision_numeric_op = True

        return out