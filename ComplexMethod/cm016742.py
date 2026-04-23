def forward(self, z, **kwargs):
        # timestep embedding
        temb = None

        # z to block_in
        h = conv_carry_causal_3d([z], self.conv_in)

        # middle
        h = self.mid.block_1(h, temb, **kwargs)
        h = self.mid.attn_1(h, **kwargs)
        h = self.mid.block_2(h, temb, **kwargs)

        if self.carried:
            h = torch.split(h, 2, dim=2)
        else:
            h = [ h ]
        out = []

        conv_carry_in = None

        # upsampling
        for i, h1 in enumerate(h):
            conv_carry_out = []
            if i == len(h) - 1:
                conv_carry_out = None
            for i_level in reversed(range(self.num_resolutions)):
                for i_block in range(self.num_res_blocks+1):
                    h1 = self.up[i_level].block[i_block](h1, temb, conv_carry_in, conv_carry_out, **kwargs)
                    if len(self.up[i_level].attn) > 0:
                        assert i == 0 #carried should not happen if attn exists
                        h1 = self.up[i_level].attn[i_block](h1, **kwargs)
                if i_level != 0:
                    h1 = self.up[i_level].upsample(h1, conv_carry_in, conv_carry_out)

            h1 = self.norm_out(h1)
            h1 = [ nonlinearity(h1) ]
            h1 = conv_carry_causal_3d(h1, self.conv_out, conv_carry_in, conv_carry_out)
            if self.tanh_out:
                h1 = torch.tanh(h1)
            out.append(h1)
            conv_carry_in = conv_carry_out

        out = torch_cat_if_needed(out, dim=2)

        return out