def forward(self, img0, img1, timestep=0.5, cache=None):
        if not isinstance(timestep, torch.Tensor):
            timestep = torch.full((img0.shape[0], 1, img0.shape[2], img0.shape[3]), timestep, device=img0.device, dtype=img0.dtype)

        self._build_warp_grids(img0.shape[2], img0.shape[3], img0.device)

        B = img0.shape[0]
        f0 = cache["img0"].expand(B, -1, -1, -1) if cache and "img0" in cache else self.encode(img0)
        f1 = cache["img1"].expand(B, -1, -1, -1) if cache and "img1" in cache else self.encode(img1)
        flow = mask = feat = None
        warped_img0, warped_img1 = img0, img1
        for i, block in enumerate(self.blocks):
            if flow is None:
                flow, mask, feat = block(torch.cat((img0, img1, f0, f1, timestep), 1), None, scale=self.scale_list[i])
            else:
                fd, mask, feat = block(
                    torch.cat((warped_img0, warped_img1, self.warp(f0, flow[:, :2]), self.warp(f1, flow[:, 2:4]), timestep, mask, feat), 1),
                    flow, scale=self.scale_list[i])
                flow = flow.add_(fd)
            warped_img0 = self.warp(img0, flow[:, :2])
            warped_img1 = self.warp(img1, flow[:, 2:4])
        return torch.lerp(warped_img1, warped_img0, torch.sigmoid(mask))