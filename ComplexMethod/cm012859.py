def __init__(
        self,
        observer,
        quant_min=0,
        quant_max=255,
        scale=1.0,
        zero_point=0.0,
        channel_len=-1,
        use_grad_scaling=False,
        **observer_kwargs,
    ):
        super().__init__()
        if quant_min >= quant_max:
            raise AssertionError("quant_min must be strictly less than quant_max.")
        self.quant_min = quant_min
        self.quant_max = quant_max
        # also pass quant_min and quant_max to observer
        observer_kwargs["quant_min"] = quant_min
        observer_kwargs["quant_max"] = quant_max
        self.use_grad_scaling = use_grad_scaling
        if channel_len == -1:
            self.scale = Parameter(torch.tensor([scale]))
            self.zero_point = Parameter(torch.tensor([zero_point]))
        else:
            if not (isinstance(channel_len, int) and channel_len > 0):
                raise AssertionError("Channel size must be a positive integer.")
            self.scale = Parameter(torch.tensor([scale] * channel_len))
            self.zero_point = Parameter(torch.tensor([zero_point] * channel_len))

        self.activation_post_process = observer(**observer_kwargs)
        if torch.iinfo(self.activation_post_process.dtype).min > quant_min:
            raise AssertionError("quant_min out of bound")
        if quant_max > torch.iinfo(self.activation_post_process.dtype).max:
            raise AssertionError("quant_max out of bound")
        self.dtype = self.activation_post_process.dtype
        self.qscheme = self.activation_post_process.qscheme
        self.ch_axis = (
            self.activation_post_process.ch_axis
            if hasattr(self.activation_post_process, "ch_axis")
            else -1
        )
        self.register_buffer("fake_quant_enabled", torch.tensor([1], dtype=torch.uint8))
        self.register_buffer("static_enabled", torch.tensor([1], dtype=torch.uint8))
        self.register_buffer("learning_enabled", torch.tensor([0], dtype=torch.uint8))

        bitrange = torch.tensor(quant_max - quant_min + 1).double()
        self.bitwidth = int(torch.log2(bitrange).item())
        self.register_buffer("eps", torch.tensor([torch.finfo(torch.float32).eps]))