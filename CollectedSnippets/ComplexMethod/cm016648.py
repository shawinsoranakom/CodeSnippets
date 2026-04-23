def forward(self, x):
        if not self.refiner_vae and x.shape[2] == 1:
            x = x.expand(-1, -1, self.ffactor_temporal, -1, -1)

        if self.refiner_vae:
            xl = [x[:, :, :1, :, :]]
            if x.shape[2] > self.ffactor_temporal:
                xl += torch.split(x[:, :, 1: 1 + ((x.shape[2] - 1) // self.ffactor_temporal) * self.ffactor_temporal, :, :], self.ffactor_temporal * 2, dim=2)
            x = xl
        else:
            x = [x]
        out = []

        conv_carry_in = None

        for i, x1 in enumerate(x):
            conv_carry_out = []
            if i == len(x) - 1:
                conv_carry_out = None

            x1 = [ x1 ]
            x1 = conv_carry_causal_3d(x1, self.conv_in, conv_carry_in, conv_carry_out)

            for stage in self.down:
                for blk in stage.block:
                    x1 = blk(x1, None, conv_carry_in, conv_carry_out)
                if hasattr(stage, 'downsample'):
                    x1 = stage.downsample(x1, conv_carry_in, conv_carry_out)

            out.append(x1)
            conv_carry_in = conv_carry_out

        out = torch_cat_if_needed(out, dim=2)

        x = self.mid.block_2(self.mid.attn_1(self.mid.block_1(out)))
        del out

        b, c, t, h, w = x.shape
        grp = c // (self.z_channels << 1)
        skip = x.view(b, c // grp, grp, t, h, w).mean(2)

        out = conv_carry_causal_3d([F.silu(self.norm_out(x))], self.conv_out) + skip

        if self.refiner_vae:
            out = self.regul(out)[0]

        return out