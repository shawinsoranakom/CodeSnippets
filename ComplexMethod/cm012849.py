def __init__(
        self,
        observer=MovingAverageMinMaxObserver,
        quant_min=None,
        quant_max=None,
        is_dynamic=False,
        **observer_kwargs,
    ):
        super().__init__()
        # Populate quant_min/quant_max to observer_kwargs if valid
        if quant_min is not None and quant_max is not None:
            if quant_min > quant_max:
                raise AssertionError(
                    "quant_min must be less than or equal to quant_max"
                )
            dtype = observer_kwargs.get("dtype", torch.quint8)
            if hasattr(observer, "p"):
                # In case observer is _PartialWrapper, dtype can be stored in
                # observer.p.keywords["dtype"]
                dtype = getattr(getattr(observer, "p", {}), "keywords", {}).get(
                    "dtype", dtype
                )

            if torch.iinfo(dtype).min > quant_min:
                raise AssertionError("quant_min out of bound")

            if quant_max > torch.iinfo(dtype).max:
                raise AssertionError("quant_max out of bound")
            observer_kwargs.update({"quant_min": quant_min, "quant_max": quant_max})
        observer_kwargs["is_dynamic"] = is_dynamic
        self.activation_post_process = observer(**observer_kwargs)
        # TODO: keeping self.quant_min/max for BC; remove after a couple releases
        # Users should use self.activation_post_process.quant_min
        self.quant_min = self.activation_post_process.quant_min
        self.quant_max = self.activation_post_process.quant_max
        self.is_dynamic = self.activation_post_process.is_dynamic
        if _is_float_qparams(self.activation_post_process.qscheme):
            zero_point_dtype = torch.float
        else:
            zero_point_dtype = torch.int
        self.register_buffer("scale", torch.tensor([1.0], dtype=torch.float))
        self.register_buffer("zero_point", torch.tensor([0], dtype=zero_point_dtype))
        self.dtype = self.activation_post_process.dtype
        self.qscheme = self.activation_post_process.qscheme
        self.ch_axis = (
            self.activation_post_process.ch_axis
            if hasattr(self.activation_post_process, "ch_axis")
            else -1
        )
        if not (_is_per_channel(self.qscheme) or _is_per_tensor(self.qscheme)):
            raise AssertionError(
                "Only per channel and per tensor quantization are supported in fake quantize"
                + " got qscheme: "
                + str(self.qscheme)
            )
        self.is_per_channel = _is_per_channel(self.qscheme)