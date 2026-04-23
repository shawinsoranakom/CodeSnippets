def masks(self, masks, colors, im_gpu: torch.Tensor = None, alpha: float = 0.5, retina_masks: bool = False):
        """Plot masks on image.

        Args:
            masks (torch.Tensor | np.ndarray): Predicted masks with shape [n, h, w].
            colors (list[list[int]]): Colors for predicted masks, [[r, g, b] * n].
            im_gpu (torch.Tensor | None): Image on GPU with shape [3, h, w], range [0, 1].
            alpha (float, optional): Mask transparency: 0.0 fully transparent, 1.0 opaque.
            retina_masks (bool, optional): Whether to use high resolution masks or not.
        """
        if self.pil:
            # Convert to numpy first
            self.im = np.asarray(self.im).copy()
        if im_gpu is None:
            assert isinstance(masks, np.ndarray), "`masks` must be a np.ndarray if `im_gpu` is not provided."
            overlay = self.im.copy()
            for i, mask in enumerate(masks):
                overlay[mask.astype(bool)] = colors[i]
            self.im = cv2.addWeighted(self.im, 1 - alpha, overlay, alpha, 0)
        else:
            assert isinstance(masks, torch.Tensor), "'masks' must be a torch.Tensor if 'im_gpu' is provided."
            if len(masks) == 0:
                self.im[:] = im_gpu.permute(1, 2, 0).contiguous().cpu().numpy() * 255
                return
            if im_gpu.device != masks.device:
                im_gpu = im_gpu.to(masks.device)

            ih, iw = self.im.shape[:2]
            if not retina_masks:
                # Use scale_masks to properly remove padding and upsample, convert bool to float first
                masks = ops.scale_masks(masks[None].float(), (ih, iw))[0] > 0.5
                # Convert original BGR image to RGB tensor
                im_gpu = (
                    torch.from_numpy(self.im).to(masks.device).permute(2, 0, 1).flip(0).contiguous().float() / 255.0
                )

            colors = torch.tensor(colors, device=masks.device, dtype=torch.float32) / 255.0  # shape(n,3)
            colors = colors[:, None, None]  # shape(n,1,1,3)
            masks = masks.unsqueeze(3)  # shape(n,h,w,1)
            masks_color = masks * (colors * alpha)  # shape(n,h,w,3)
            inv_alpha_masks = (1 - masks * alpha).cumprod(0)  # shape(n,h,w,1)
            mcs = masks_color.max(dim=0).values  # shape(h,w,3)

            im_gpu = im_gpu.flip(dims=[0]).permute(1, 2, 0).contiguous()  # shape(h,w,3)
            im_gpu = im_gpu * inv_alpha_masks[-1] + mcs
            self.im[:] = (im_gpu * 255).byte().cpu().numpy()
        if self.pil:
            # Convert im back to PIL and update draw
            self.fromarray(self.im)