def __init__(
        self,
        inplanes,
        ratio,
        headers,
        pooling_type="att",
        att_scale=False,
        fusion_type="channel_add",
    ):
        super(MultiAspectGCAttention, self).__init__()
        assert pooling_type in ["avg", "att"]

        assert fusion_type in ["channel_add", "channel_mul", "channel_concat"]
        assert (
            inplanes % headers == 0 and inplanes >= 8
        )  # inplanes must be divided by headers evenly

        self.headers = headers
        self.inplanes = inplanes
        self.ratio = ratio
        self.planes = int(inplanes * ratio)
        self.pooling_type = pooling_type
        self.fusion_type = fusion_type
        self.att_scale = False

        self.single_header_inplanes = int(inplanes / headers)

        if pooling_type == "att":
            self.conv_mask = nn.Conv2D(self.single_header_inplanes, 1, kernel_size=1)
            self.softmax = nn.Softmax(axis=2)
        else:
            self.avg_pool = nn.AdaptiveAvgPool2D(1)

        if fusion_type == "channel_add":
            self.channel_add_conv = nn.Sequential(
                nn.Conv2D(self.inplanes, self.planes, kernel_size=1),
                nn.LayerNorm([self.planes, 1, 1]),
                nn.ReLU(),
                nn.Conv2D(self.planes, self.inplanes, kernel_size=1),
            )
        elif fusion_type == "channel_concat":
            self.channel_concat_conv = nn.Sequential(
                nn.Conv2D(self.inplanes, self.planes, kernel_size=1),
                nn.LayerNorm([self.planes, 1, 1]),
                nn.ReLU(),
                nn.Conv2D(self.planes, self.inplanes, kernel_size=1),
            )
            # for concat
            self.cat_conv = nn.Conv2D(2 * self.inplanes, self.inplanes, kernel_size=1)
        elif fusion_type == "channel_mul":
            self.channel_mul_conv = nn.Sequential(
                nn.Conv2D(self.inplanes, self.planes, kernel_size=1),
                nn.LayerNorm([self.planes, 1, 1]),
                nn.ReLU(),
                nn.Conv2D(self.planes, self.inplanes, kernel_size=1),
            )