def forward(self, z):
        x = conv_carry_causal_3d([z], self.conv_in) + z.repeat_interleave(self.block_out_channels[0] // self.z_channels, 1)
        x = self.mid.block_2(self.mid.attn_1(self.mid.block_1(x)))

        if self.refiner_vae:
            x = torch.split(x, 2, dim=2)
        else:
            x = [ x ]
        out = []

        conv_carry_in = None

        for i, x1 in enumerate(x):
            conv_carry_out = []
            if i == len(x) - 1:
                conv_carry_out = None
            for stage in self.up:
                for blk in stage.block:
                    x1 = blk(x1, None, conv_carry_in, conv_carry_out)
                if hasattr(stage, 'upsample'):
                    x1 = stage.upsample(x1, conv_carry_in, conv_carry_out)

            x1 = [ F.silu(self.norm_out(x1)) ]
            x1 = conv_carry_causal_3d(x1, self.conv_out, conv_carry_in, conv_carry_out)
            out.append(x1)
            conv_carry_in = conv_carry_out
        del x

        out = torch_cat_if_needed(out, dim=2)

        if not self.refiner_vae:
            if z.shape[-3] == 1:
                out = out[:, :, -1:]

        return out