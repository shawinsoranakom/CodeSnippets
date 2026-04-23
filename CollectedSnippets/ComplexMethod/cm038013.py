def __init__(
        self,
        subsampling: str,
        subsampling_factor: int,
        feat_in: int,
        feat_out: int,
        conv_channels: int,
        subsampling_conv_chunking_factor: int = 1,
        activation: nn.Module | None = None,
        is_causal: bool = False,
    ) -> None:
        super().__init__()
        if activation is None:
            activation = nn.ReLU()

        if subsampling_factor % 2 != 0:
            raise ValueError("Sampling factor should be a multiply of 2!")
        self._sampling_num = int(math.log(subsampling_factor, 2))

        if (
            subsampling_conv_chunking_factor != -1
            and subsampling_conv_chunking_factor != 1
            and subsampling_conv_chunking_factor % 2 != 0
        ):
            raise ValueError(
                "subsampling_conv_chunking_factor should be -1, 1, or a power of 2"
            )

        in_channels = 1
        layers = []

        assert subsampling == "dw_striding"
        self._stride = 2
        self._kernel_size = 3
        self._ceil_mode = False

        assert not is_causal

        self._left_padding = (self._kernel_size - 1) // 2
        self._right_padding = (self._kernel_size - 1) // 2

        # Layer 1
        # [1, T, num_melspec] -> [conv_channels, T//2, num_melspec//2]
        layers.append(
            torch.nn.Conv2d(
                in_channels=in_channels,
                out_channels=conv_channels,
                kernel_size=self._kernel_size,
                stride=self._stride,
                padding=self._left_padding,
            )
        )
        in_channels = conv_channels
        layers.append(activation)

        for i in range(self._sampling_num - 1):
            # [conv_channels, T//2^i, num_melspec//2^i] ->
            # [conv_channels, T//2^(i+1), num_melspec//2^(i+1)]
            # depthwise conv
            layers.append(
                torch.nn.Conv2d(
                    in_channels=in_channels,
                    out_channels=in_channels,
                    kernel_size=self._kernel_size,
                    stride=self._stride,
                    padding=self._left_padding,
                    groups=in_channels,
                )
            )

            # [conv_channels, T//2^(i+1), num_melspec//2^(i+1)]
            # -> [conv_channels, T//2^(i+1), num_melspec//2^(i+1)]
            # pointwise conv
            layers.append(
                torch.nn.Conv2d(
                    in_channels=in_channels,
                    out_channels=conv_channels,
                    kernel_size=1,
                    stride=1,
                    padding=0,
                    groups=1,
                )
            )
            layers.append(activation)
            in_channels = conv_channels

        in_length = torch.tensor(feat_in, dtype=torch.float)
        out_length = self.calc_length(
            lengths=in_length,
            all_paddings=self._left_padding + self._right_padding,
            kernel_size=self._kernel_size,
            stride=self._stride,
            ceil_mode=self._ceil_mode,
            repeat_num=self._sampling_num,
        )

        # reshape:
        # [conv_channels, T//sub_factor, num_melspec//sub_factor]
        # -> [T//sub_factor, conv_channels * (num_melspec//sub_factor)]
        # mlp:
        # [T//sub_factor, conv_channels * (num_melspec//sub_factor)]
        # -> [T//sub_factor, feat_out]
        self.out = torch.nn.Linear(conv_channels * int(out_length), feat_out)
        self.conv2d_subsampling = True
        self.conv = MaskedConvSequential(*layers)