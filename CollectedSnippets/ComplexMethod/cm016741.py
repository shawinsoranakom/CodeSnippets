def __init__(self, *, ch, out_ch, ch_mult=(1,2,4,8), num_res_blocks,
                 attn_resolutions, dropout=0.0, resamp_with_conv=True, in_channels,
                 resolution, z_channels, tanh_out=False, use_linear_attn=False,
                 conv_out_op=ops.Conv2d,
                 resnet_op=ResnetBlock,
                 attn_op=AttnBlock,
                 conv3d=False,
                 time_compress=None,
                **ignorekwargs):
        super().__init__()
        self.ch = ch
        self.temb_ch = 0
        self.num_resolutions = len(ch_mult)
        self.num_res_blocks = num_res_blocks
        self.resolution = resolution
        self.in_channels = in_channels
        self.tanh_out = tanh_out
        self.carried = False

        if conv3d:
            if not attn_resolutions and resnet_op == ResnetBlock:
                conv_op = CarriedConv3d
                conv_out_op = CarriedConv3d
                self.carried = True
            else:
                conv_op = VideoConv3d
                conv_out_op = VideoConv3d

            mid_attn_conv_op = ops.Conv3d
        else:
            conv_op = ops.Conv2d
            mid_attn_conv_op = ops.Conv2d

        # compute block_in and curr_res at lowest res
        block_in = ch*ch_mult[self.num_resolutions-1]
        curr_res = resolution // 2**(self.num_resolutions-1)
        self.z_shape = (1,z_channels,curr_res,curr_res)
        logging.debug("Working with z of shape {} = {} dimensions.".format(
            self.z_shape, np.prod(self.z_shape)))

        # z to block_in
        self.conv_in = conv_op(z_channels,
                                       block_in,
                                       kernel_size=3,
                                       stride=1,
                                       padding=1)

        # middle
        self.mid = nn.Module()
        self.mid.block_1 = resnet_op(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=self.temb_ch,
                                       dropout=dropout,
                                       conv_op=conv_op)
        self.mid.attn_1 = attn_op(block_in, conv_op=mid_attn_conv_op)
        self.mid.block_2 = resnet_op(in_channels=block_in,
                                       out_channels=block_in,
                                       temb_channels=self.temb_ch,
                                       dropout=dropout,
                                       conv_op=conv_op)

        # upsampling
        self.up = nn.ModuleList()
        for i_level in reversed(range(self.num_resolutions)):
            block = nn.ModuleList()
            attn = nn.ModuleList()
            block_out = ch*ch_mult[i_level]
            for i_block in range(self.num_res_blocks+1):
                block.append(resnet_op(in_channels=block_in,
                                         out_channels=block_out,
                                         temb_channels=self.temb_ch,
                                         dropout=dropout,
                                         conv_op=conv_op))
                block_in = block_out
                if curr_res in attn_resolutions:
                    attn.append(attn_op(block_in, conv_op=conv_op))
            up = nn.Module()
            up.block = block
            up.attn = attn
            if i_level != 0:
                scale_factor = 2.0
                if time_compress is not None:
                    if i_level > math.log2(time_compress):
                        scale_factor = (1.0, 2.0, 2.0)

                up.upsample = Upsample(block_in, resamp_with_conv, conv_op=conv_op, scale_factor=scale_factor)
                curr_res = curr_res * 2
            self.up.insert(0, up) # prepend to get consistent order

        # end
        self.norm_out = Normalize(block_in)
        self.conv_out = conv_out_op(block_in,
                                        out_ch,
                                        kernel_size=3,
                                        stride=1,
                                        padding=1)