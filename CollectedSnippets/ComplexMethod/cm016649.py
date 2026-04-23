def __init__(self, z_channels, out_channels, block_out_channels, num_res_blocks,
                 ffactor_spatial, ffactor_temporal, upsample_match_channel=True, refiner_vae=True, **_):
        super().__init__()
        block_out_channels = block_out_channels[::-1]
        self.z_channels = z_channels
        self.block_out_channels = block_out_channels
        self.num_res_blocks = num_res_blocks

        self.refiner_vae = refiner_vae
        if self.refiner_vae:
            conv_op = CarriedConv3d
            norm_op = RMS_norm
        else:
            conv_op = ops.Conv3d
            norm_op = Normalize

        ch = block_out_channels[0]
        self.conv_in = conv_op(z_channels, ch, kernel_size=3, stride=1, padding=1)

        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=ch, out_channels=ch, conv_op=conv_op, norm_op=norm_op)
        self.mid.attn_1 = AttnBlock(ch, conv_op=ops.Conv3d, norm_op=norm_op)
        self.mid.block_2 = ResnetBlock(in_channels=ch, out_channels=ch,  conv_op=conv_op, norm_op=norm_op)

        self.up = nn.ModuleList()
        depth = (ffactor_spatial >> 1).bit_length()
        depth_temporal = (ffactor_temporal >> 1).bit_length()

        for i, tgt in enumerate(block_out_channels):
            stage = nn.Module()
            stage.block = nn.ModuleList([ResnetBlock(in_channels=ch if j == 0 else tgt,
                                                     out_channels=tgt,
                                                     temb_channels=0,
                                                     conv_op=conv_op, norm_op=norm_op)
                                        for j in range(num_res_blocks + 1)])
            ch = tgt
            if i < depth:
                nxt = block_out_channels[i + 1] if i + 1 < len(block_out_channels) and upsample_match_channel else ch
                stage.upsample = UpSmpl(ch, nxt, tus=i < depth_temporal, refiner_vae=self.refiner_vae, op=conv_op)
                ch = nxt
            self.up.append(stage)

        self.norm_out = norm_op(ch)
        self.conv_out = conv_op(ch, out_channels, 3, stride=1, padding=1)