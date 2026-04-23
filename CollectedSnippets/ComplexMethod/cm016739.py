def __init__(self, *, ch, out_ch, ch_mult=(1,2,4,8), num_res_blocks,
                 attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels,
                 resolution, z_channels, double_z=True, use_linear_attn=False, attn_type="vanilla",
                 conv3d=False, time_compress=None,
                 **ignore_kwargs):
        super().__init__()
        if use_linear_attn:
            attn_type = "linear"
        self.ch = ch
        self.temb_ch = 0
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        self.resolution = resolution
        self.in_channels = in_channels
        self.carried = False

        if conv3d:
            if not attn_resolutions:
                conv_op = CarriedConv3d
                self.carried = True
            else:
                conv_op = VideoConv3d
            mid_attn_conv_op = ops.Conv3d
        else:
            conv_op = ops.Conv2d
            mid_attn_conv_op = ops.Conv2d

        # downsampling
        self.conv_in = conv_op(in_channels,
                                       self.ch,
                                       kernel_size=3,
                                       stride=1,
                                       padding=1)

        self.time_compress = 1
        curr_res = resolution
        in_ch_mult = (1,)+tuple(ch_mult)
        self.in_ch_mult = in_ch_mult
        self.down = nn.ModuleList()
        for i_level in range(self.num_resolutions):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_in = ch*in_ch_mult[i_level]
            block_out = ch*ch_mult[i_level]
            for i_block in range(self.num_res_blocks):
                block.append(ResnetBlock(in_channels=block_in,
                                         out_channels=block_out,
                                         temb_channels=self.temb_ch,
                                         dropout=dropout,
                                         conv_op=conv_op))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(make_attn(block_in, attn_type=attn_type, conv_op=conv_op))
            down = nn.Module()
            down.block = block
            down.attn = attn
            if i_level != self.num_resolutions-1:
                stride = 2
                if time_compress is not None:
                    if (self.num_resolutions - 1 - i_level) > math.log2(time_compress):
                        stride = (1, 2, 2)
                else:
                    self.time_compress *= 2
                down.downsample = Downsample(block_in, resamp_with_conv, stride=stride, conv_op=conv_op)
                curr_res = curr_res // 2
            self.down.append(down)

        if time_compress is not None:
            self.time_compress = time_compress

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=self.temb_ch,
                                       dropout=dropout,
                                       conv_op=conv_op)
        self.mid.attn_1 = make_attn(block_in, attn_type=attn_type, conv_op=mid_attn_conv_op)
        self.mid.block_2 = ResnetBlock(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=self.temb_ch,
                                       dropout=dropout,
                                       conv_op=conv_op)

        # end
        self.norm_out = Normalize(block_in)
        self.conv_out = conv_op(block_in,
                                        2*z_channels if double_z else z_channels,
                                        kernel_size=3,
                                        stride=1,
                                        padding=1)