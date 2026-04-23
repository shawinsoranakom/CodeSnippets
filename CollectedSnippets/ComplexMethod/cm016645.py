def forward(self, x, conv_carry_in=None, conv_carry_out=None):
        r1 = 2 if self.tds else 1
        h = conv_carry_causal_3d([x], self.conv, conv_carry_in, conv_carry_out)

        if self.tds and self.refiner_vae and conv_carry_in is None:

            hf = h[:, :, :1, :, :]
            b, c, f, ht, wd = hf.shape
            hf = hf.reshape(b, c, f, ht // 2, 2, wd // 2, 2)
            hf = hf.permute(0, 4, 6, 1, 2, 3, 5)
            hf = hf.reshape(b, 2 * 2 * c, f, ht // 2, wd // 2)
            hf = torch.cat([hf, hf], dim=1)

            h = h[:, :, 1:, :, :]

            xf = x[:, :, :1, :, :]
            b, ci, f, ht, wd = xf.shape
            xf = xf.reshape(b, ci, f, ht // 2, 2, wd // 2, 2)
            xf = xf.permute(0, 4, 6, 1, 2, 3, 5)
            xf = xf.reshape(b, 2 * 2 * ci, f, ht // 2, wd // 2)
            B, C, T, H, W = xf.shape
            xf = xf.view(B, hf.shape[1], self.gs // 2, T, H, W).mean(dim=2)

            x = x[:, :, 1:, :, :]

        if h.shape[2] == 0:
            return hf + xf

        b, c, frms, ht, wd = h.shape
        nf = frms // r1
        h = h.reshape(b, c, nf, r1, ht // 2, 2, wd // 2, 2)
        h = h.permute(0, 3, 5, 7, 1, 2, 4, 6)
        h = h.reshape(b, r1 * 2 * 2 * c, nf, ht // 2, wd // 2)

        b, ci, frms, ht, wd = x.shape
        nf = frms // r1
        x = x.reshape(b, ci, nf, r1, ht // 2, 2, wd // 2, 2)
        x = x.permute(0, 3, 5, 7, 1, 2, 4, 6)
        x = x.reshape(b, r1 * 2 * 2 * ci, nf, ht // 2, wd // 2)
        B, C, T, H, W = x.shape
        x = x.view(B, h.shape[1], self.gs, T, H, W).mean(dim=2)

        if self.tds and self.refiner_vae and conv_carry_in is None:
            h = torch.cat([hf, h], dim=2)
            x = torch.cat([xf, x], dim=2)

        return h + x