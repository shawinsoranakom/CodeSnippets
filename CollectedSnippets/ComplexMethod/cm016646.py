def forward(self, x, conv_carry_in=None, conv_carry_out=None):
        r1 = 2 if self.tus else 1
        h = conv_carry_causal_3d([x], self.conv, conv_carry_in, conv_carry_out)

        if self.tus and self.refiner_vae and conv_carry_in is None:
            hf = h[:, :, :1, :, :]
            b, c, f, ht, wd = hf.shape
            nc = c // (2 * 2)
            hf = hf.reshape(b, 2, 2, nc, f, ht, wd)
            hf = hf.permute(0, 3, 4, 5, 1, 6, 2)
            hf = hf.reshape(b, nc, f, ht * 2, wd * 2)
            hf = hf[:, : hf.shape[1] // 2]

            h = h[:, :, 1:, :, :]

            xf = x[:, :, :1, :, :]
            b, ci, f, ht, wd = xf.shape
            xf = xf.repeat_interleave(repeats=self.rp // 2, dim=1)
            b, c, f, ht, wd = xf.shape
            nc = c // (2 * 2)
            xf = xf.reshape(b, 2, 2, nc, f, ht, wd)
            xf = xf.permute(0, 3, 4, 5, 1, 6, 2)
            xf = xf.reshape(b, nc, f, ht * 2, wd * 2)

            x = x[:, :, 1:, :, :]

        b, c, frms, ht, wd = h.shape
        nc = c // (r1 * 2 * 2)
        h = h.reshape(b, r1, 2, 2, nc, frms, ht, wd)
        h = h.permute(0, 4, 5, 1, 6, 2, 7, 3)
        h = h.reshape(b, nc, frms * r1, ht * 2, wd * 2)

        x = x.repeat_interleave(repeats=self.rp, dim=1)
        b, c, frms, ht, wd = x.shape
        nc = c // (r1 * 2 * 2)
        x = x.reshape(b, r1, 2, 2, nc, frms, ht, wd)
        x = x.permute(0, 4, 5, 1, 6, 2, 7, 3)
        x = x.reshape(b, nc, frms * r1, ht * 2, wd * 2)

        if self.tus and self.refiner_vae and conv_carry_in is None:
            h = torch.cat([hf, h], dim=2)
            x = torch.cat([xf, x], dim=2)

        return h + x