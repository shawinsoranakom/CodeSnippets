def concat_cond(self, **kwargs):
        noise = kwargs.get("noise", None)
        extra_channels = self.diffusion_model.patch_embedding.weight.shape[1] - noise.shape[1]
        if extra_channels == 0:
            return None

        image = kwargs.get("concat_latent_image", None)
        device = kwargs["device"]

        if image is None:
            shape_image = list(noise.shape)
            shape_image[1] = extra_channels
            image = torch.zeros(shape_image, dtype=noise.dtype, layout=noise.layout, device=noise.device)
        else:
            latent_dim = self.latent_format.latent_channels
            image = utils.common_upscale(image.to(device), noise.shape[-1], noise.shape[-2], "bilinear", "center")
            for i in range(0, image.shape[1], latent_dim):
                image[:, i: i + latent_dim] = self.process_latent_in(image[:, i: i + latent_dim])
            image = utils.resize_to_batch_size(image, noise.shape[0])

        if extra_channels != image.shape[1] + 4:
            if not self.image_to_video or extra_channels == image.shape[1]:
                return image

        if image.shape[1] > (extra_channels - 4):
            image = image[:, :(extra_channels - 4)]

        mask = kwargs.get("concat_mask", kwargs.get("denoise_mask", None))
        if mask is None:
            mask = torch.zeros_like(noise)[:, :4]
        else:
            if mask.shape[1] != 4:
                mask = torch.mean(mask, dim=1, keepdim=True)
            mask = 1.0 - mask
            mask = utils.common_upscale(mask.to(device), noise.shape[-1], noise.shape[-2], "bilinear", "center")
            if mask.shape[-3] < noise.shape[-3]:
                mask = torch.nn.functional.pad(mask, (0, 0, 0, 0, 0, noise.shape[-3] - mask.shape[-3]), mode='constant', value=0)
            if mask.shape[1] == 1:
                mask = mask.repeat(1, 4, 1, 1, 1)
            mask = utils.resize_to_batch_size(mask, noise.shape[0])

        concat_mask_index = kwargs.get("concat_mask_index", 0)
        if concat_mask_index != 0:
            return torch.cat((image[:, :concat_mask_index], mask, image[:, concat_mask_index:]), dim=1)
        else:
            return torch.cat((mask, image), dim=1)