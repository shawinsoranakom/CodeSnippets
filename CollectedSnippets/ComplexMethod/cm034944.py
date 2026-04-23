def __init__(self, in_channels, out_channels_list, **kwargs):
        super().__init__()
        self.head_list = kwargs.pop("head_list")
        self.use_pool = kwargs.get("use_pool", False)
        self.use_pos = kwargs.get("use_pos", False)
        self.in_channels = in_channels
        if self.use_pool:
            self.pool = nn.AvgPool2D(kernel_size=[3, 2], stride=[3, 2], padding=0)
        self.gtc_head = "sar"
        assert len(self.head_list) >= 2
        for idx, head_name in enumerate(self.head_list):
            name = list(head_name)[0]
            if name == "SARHead":
                # sar head
                sar_args = self.head_list[idx][name]
                self.sar_head = eval(name)(
                    in_channels=in_channels,
                    out_channels=out_channels_list["SARLabelDecode"],
                    **sar_args,
                )
            elif name == "NRTRHead":
                gtc_args = self.head_list[idx][name]
                max_text_length = gtc_args.get("max_text_length", 25)
                nrtr_dim = gtc_args.get("nrtr_dim", 256)
                num_decoder_layers = gtc_args.get("num_decoder_layers", 4)
                if self.use_pos:
                    self.before_gtc = nn.Sequential(
                        nn.Flatten(2),
                        FCTranspose(in_channels, nrtr_dim),
                        AddPos(nrtr_dim, 80),
                    )
                else:
                    self.before_gtc = nn.Sequential(
                        nn.Flatten(2), FCTranspose(in_channels, nrtr_dim)
                    )

                self.gtc_head = Transformer(
                    d_model=nrtr_dim,
                    nhead=nrtr_dim // 32,
                    num_encoder_layers=-1,
                    beam_size=-1,
                    num_decoder_layers=num_decoder_layers,
                    max_len=max_text_length,
                    dim_feedforward=nrtr_dim * 4,
                    out_channels=out_channels_list["NRTRLabelDecode"],
                )
            elif name == "CTCHead":
                # ctc neck
                self.encoder_reshape = Im2Seq(in_channels)
                neck_args = self.head_list[idx][name]["Neck"]
                encoder_type = neck_args.pop("name")
                self.ctc_encoder = SequenceEncoder(
                    in_channels=in_channels, encoder_type=encoder_type, **neck_args
                )
                # ctc head
                head_args = self.head_list[idx][name]["Head"]
                self.ctc_head = eval(name)(
                    in_channels=self.ctc_encoder.out_channels,
                    out_channels=out_channels_list["CTCLabelDecode"],
                    **head_args,
                )
            else:
                raise NotImplementedError(
                    "{} is not supported in MultiHead yet".format(name)
                )