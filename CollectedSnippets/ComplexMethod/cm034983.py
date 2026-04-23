def __init__(
        self,
        in_channels=3,
        scale_factor=2,
        width=128,
        height=32,
        STN=True,
        srb_nums=5,
        mask=False,
        hidden_units=32,
        infer_mode=False,
    ):
        super(TBSRN, self).__init__()
        in_planes = 3
        if mask:
            in_planes = 4
        assert math.log(scale_factor, 2) % 1 == 0
        upsample_block_num = int(math.log(scale_factor, 2))
        self.block1 = nn.Sequential(
            nn.Conv2D(in_planes, 2 * hidden_units, kernel_size=9, padding=4),
            nn.PReLU(),
            # nn.ReLU()
        )
        self.srb_nums = srb_nums
        for i in range(srb_nums):
            setattr(self, "block%d" % (i + 2), RecurrentResidualBlock(2 * hidden_units))

        setattr(
            self,
            "block%d" % (srb_nums + 2),
            nn.Sequential(
                nn.Conv2D(2 * hidden_units, 2 * hidden_units, kernel_size=3, padding=1),
                nn.BatchNorm2D(2 * hidden_units),
            ),
        )

        # self.non_local = NonLocalBlock2D(64, 64)
        block_ = [UpsampleBLock(2 * hidden_units, 2) for _ in range(upsample_block_num)]
        block_.append(nn.Conv2D(2 * hidden_units, in_planes, kernel_size=9, padding=4))
        setattr(self, "block%d" % (srb_nums + 3), nn.Sequential(*block_))
        self.tps_inputsize = [height // scale_factor, width // scale_factor]
        tps_outputsize = [height // scale_factor, width // scale_factor]
        num_control_points = 20
        tps_margins = [0.05, 0.05]
        self.stn = STN
        self.out_channels = in_channels
        if self.stn:
            self.tps = TPSSpatialTransformer(
                output_image_size=tuple(tps_outputsize),
                num_control_points=num_control_points,
                margins=tuple(tps_margins),
            )

            self.stn_head = STNHead(
                in_channels=in_planes,
                num_ctrlpoints=num_control_points,
                activation="none",
            )
        self.infer_mode = infer_mode

        self.english_alphabet = (
            "-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )
        self.english_dict = {}
        for index in range(len(self.english_alphabet)):
            self.english_dict[self.english_alphabet[index]] = index
        transformer = Transformer(alphabet="-0123456789abcdefghijklmnopqrstuvwxyz")
        self.transformer = transformer
        for param in self.transformer.parameters():
            param.trainable = False