def forward(self, x):
        # timestep embedding
        temb = None

        if self.carried:
            xl = [x[:, :, :1, :, :]]
            if x.shape[2] > self.time_compress:
                tc = self.time_compress
                xl += torch.split(x[:, :, 1: 1 + ((x.shape[2] - 1) // tc) * tc, :, :], tc * 2, dim = 2)
            x = xl
        else:
            x = [x]
        out = []

        conv_carry_in = None

        for i, x1 in enumerate(x):
            conv_carry_out = []
            if i == len(x) - 1:
                conv_carry_out = None

            # downsampling
            x1 = [ x1 ]
            h1 = conv_carry_causal_3d(x1, self.conv_in, conv_carry_in, conv_carry_out)

            for i_level in range(self.num_resolutions):
                for i_block in range(self.num_res_blocks):
                    h1 = self.down[i_level].block[i_block](h1, temb, conv_carry_in, conv_carry_out)
                    if len(self.down[i_level].attn) > 0:
                        assert i == 0 #carried should not happen if attn exists
                        h1 = self.down[i_level].attn[i_block](h1)
                if i_level != self.num_resolutions-1:
                    h1 = self.down[i_level].downsample(h1, conv_carry_in, conv_carry_out)

            out.append(h1)
            conv_carry_in = conv_carry_out

        h = torch_cat_if_needed(out, dim=2)
        del out

        # middle
        h = self.mid.block_1(h, temb)
        h = self.mid.attn_1(h)
        h = self.mid.block_2(h, temb)

        # end
        h = self.norm_out(h)
        h = [ nonlinearity(h) ]
        h = conv_carry_causal_3d(h, self.conv_out)
        return h