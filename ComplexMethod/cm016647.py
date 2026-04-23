def __init__(self, in_channels, z_channels, block_out_channels, num_res_blocks,
                 ffactor_spatial, ffactor_temporal, downsample_match_channel=True, refiner_vae=True, **_):
        super().__init__()
        self.z_channels = z_channels
        self.block_out_channels = block_out_channels
        self.num_res_blocks = num_res_blocks
        self.ffactor_temporal = ffactor_temporal

        self.refiner_vae = refiner_vae
        if self.refiner_vae:
            conv_op = CarriedConv3d
            norm_op = RMS_norm
        else:
            conv_op = ops.Conv3d
            norm_op = Normalize

        self.conv_in = conv_op(in_channels, block_out_channels[0], 3, 1, 1)

        self.down = nn.ModuleList()
        ch = block_out_channels[0]
        depth = (ffactor_spatial >> 1).bit_length()
        depth_temporal = ((ffactor_spatial // self.ffactor_temporal) >> 1).bit_length()

        for i, tgt in enumerate(block_out_channels):
            stage = nn.Module()
            stage.block = nn.ModuleList([ResnetBlock(in_channels=ch if j == 0 else tgt,
                                                     out_channels=tgt,
                                                     temb_channels=0,
                                                     conv_op=conv_op, norm_op=norm_op)
                                        for j in range(num_res_blocks)])
            ch = tgt
            if i < depth:
                nxt = block_out_channels[i + 1] if i + 1 < len(block_out_channels) and downsample_match_channel else ch
                stage.downsample = DnSmpl(ch, nxt, tds=i >= depth_temporal, refiner_vae=self.refiner_vae, op=conv_op)
                ch = nxt
            self.down.append(stage)

        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=ch, out_channels=ch, conv_op=conv_op, norm_op=norm_op)
        self.mid.attn_1 = AttnBlock(ch, conv_op=ops.Conv3d, norm_op=norm_op)
        self.mid.block_2 = ResnetBlock(in_channels=ch, out_channels=ch, conv_op=conv_op, norm_op=norm_op)

        self.norm_out = norm_op(ch)
        self.conv_out = conv_op(ch, z_channels << 1, 3, 1, 1)

        self.regul = comfy.ldm.models.autoencoder.DiagonalGaussianRegularizer()