def init(self, all_prompts, all_seeds, all_subseeds):
        self.extra_generation_params["Denoising strength"] = self.denoising_strength

        self.image_cfg_scale: float = self.image_cfg_scale if shared.sd_model.cond_stage_key == "edit" else None

        self.sampler = sd_samplers.create_sampler(self.sampler_name, self.sd_model)
        crop_region = None

        image_mask = self.image_mask

        if image_mask is not None:
            # image_mask is passed in as RGBA by Gradio to support alpha masks,
            # but we still want to support binary masks.
            image_mask = create_binary_mask(image_mask, round=self.mask_round)

            if self.inpainting_mask_invert:
                image_mask = ImageOps.invert(image_mask)
                self.extra_generation_params["Mask mode"] = "Inpaint not masked"

            if self.mask_blur_x > 0:
                np_mask = np.array(image_mask)
                kernel_size = 2 * int(2.5 * self.mask_blur_x + 0.5) + 1
                np_mask = cv2.GaussianBlur(np_mask, (kernel_size, 1), self.mask_blur_x)
                image_mask = Image.fromarray(np_mask)

            if self.mask_blur_y > 0:
                np_mask = np.array(image_mask)
                kernel_size = 2 * int(2.5 * self.mask_blur_y + 0.5) + 1
                np_mask = cv2.GaussianBlur(np_mask, (1, kernel_size), self.mask_blur_y)
                image_mask = Image.fromarray(np_mask)

            if self.mask_blur_x > 0 or self.mask_blur_y > 0:
                self.extra_generation_params["Mask blur"] = self.mask_blur

            if self.inpaint_full_res:
                self.mask_for_overlay = image_mask
                mask = image_mask.convert('L')
                crop_region = masking.get_crop_region_v2(mask, self.inpaint_full_res_padding)
                if crop_region:
                    crop_region = masking.expand_crop_region(crop_region, self.width, self.height, mask.width, mask.height)
                    x1, y1, x2, y2 = crop_region
                    mask = mask.crop(crop_region)
                    image_mask = images.resize_image(2, mask, self.width, self.height)
                    self.paste_to = (x1, y1, x2-x1, y2-y1)
                    self.extra_generation_params["Inpaint area"] = "Only masked"
                    self.extra_generation_params["Masked area padding"] = self.inpaint_full_res_padding
                else:
                    crop_region = None
                    image_mask = None
                    self.mask_for_overlay = None
                    self.inpaint_full_res = False
                    massage = 'Unable to perform "Inpaint Only mask" because mask is blank, switch to img2img mode.'
                    model_hijack.comments.append(massage)
                    logging.info(massage)
            else:
                image_mask = images.resize_image(self.resize_mode, image_mask, self.width, self.height)
                np_mask = np.array(image_mask)
                np_mask = np.clip((np_mask.astype(np.float32)) * 2, 0, 255).astype(np.uint8)
                self.mask_for_overlay = Image.fromarray(np_mask)

            self.overlay_images = []

        latent_mask = self.latent_mask if self.latent_mask is not None else image_mask

        add_color_corrections = opts.img2img_color_correction and self.color_corrections is None
        if add_color_corrections:
            self.color_corrections = []
        imgs = []
        for img in self.init_images:

            # Save init image
            if opts.save_init_img:
                self.init_img_hash = hashlib.md5(img.tobytes()).hexdigest()
                images.save_image(img, path=opts.outdir_init_images, basename=None, forced_filename=self.init_img_hash, save_to_dirs=False, existing_info=img.info)

            image = images.flatten(img, opts.img2img_background_color)

            if crop_region is None and self.resize_mode != 3:
                image = images.resize_image(self.resize_mode, image, self.width, self.height)

            if image_mask is not None:
                if self.mask_for_overlay.size != (image.width, image.height):
                    self.mask_for_overlay = images.resize_image(self.resize_mode, self.mask_for_overlay, image.width, image.height)
                image_masked = Image.new('RGBa', (image.width, image.height))
                image_masked.paste(image.convert("RGBA").convert("RGBa"), mask=ImageOps.invert(self.mask_for_overlay.convert('L')))

                self.overlay_images.append(image_masked.convert('RGBA'))

            # crop_region is not None if we are doing inpaint full res
            if crop_region is not None:
                image = image.crop(crop_region)
                image = images.resize_image(2, image, self.width, self.height)

            if image_mask is not None:
                if self.inpainting_fill != 1:
                    image = masking.fill(image, latent_mask)

                    if self.inpainting_fill == 0:
                        self.extra_generation_params["Masked content"] = 'fill'

            if add_color_corrections:
                self.color_corrections.append(setup_color_correction(image))

            image = np.array(image).astype(np.float32) / 255.0
            image = np.moveaxis(image, 2, 0)

            imgs.append(image)

        if len(imgs) == 1:
            batch_images = np.expand_dims(imgs[0], axis=0).repeat(self.batch_size, axis=0)
            if self.overlay_images is not None:
                self.overlay_images = self.overlay_images * self.batch_size

            if self.color_corrections is not None and len(self.color_corrections) == 1:
                self.color_corrections = self.color_corrections * self.batch_size

        elif len(imgs) <= self.batch_size:
            self.batch_size = len(imgs)
            batch_images = np.array(imgs)
        else:
            raise RuntimeError(f"bad number of images passed: {len(imgs)}; expecting {self.batch_size} or less")

        image = torch.from_numpy(batch_images)
        image = image.to(shared.device, dtype=devices.dtype_vae)

        if opts.sd_vae_encode_method != 'Full':
            self.extra_generation_params['VAE Encoder'] = opts.sd_vae_encode_method

        self.init_latent = images_tensor_to_samples(image, approximation_indexes.get(opts.sd_vae_encode_method), self.sd_model)
        devices.torch_gc()

        if self.resize_mode == 3:
            self.init_latent = torch.nn.functional.interpolate(self.init_latent, size=(self.height // opt_f, self.width // opt_f), mode="bilinear")

        if image_mask is not None:
            init_mask = latent_mask
            latmask = init_mask.convert('RGB').resize((self.init_latent.shape[3], self.init_latent.shape[2]))
            latmask = np.moveaxis(np.array(latmask, dtype=np.float32), 2, 0) / 255
            latmask = latmask[0]
            if self.mask_round:
                latmask = np.around(latmask)
            latmask = np.tile(latmask[None], (self.init_latent.shape[1], 1, 1))

            self.mask = torch.asarray(1.0 - latmask).to(shared.device).type(devices.dtype)
            self.nmask = torch.asarray(latmask).to(shared.device).type(devices.dtype)

            # this needs to be fixed to be done in sample() using actual seeds for batches
            if self.inpainting_fill == 2:
                self.init_latent = self.init_latent * self.mask + create_random_tensors(self.init_latent.shape[1:], all_seeds[0:self.init_latent.shape[0]]) * self.nmask
                self.extra_generation_params["Masked content"] = 'latent noise'

            elif self.inpainting_fill == 3:
                self.init_latent = self.init_latent * self.mask
                self.extra_generation_params["Masked content"] = 'latent nothing'

        self.image_conditioning = self.img2img_image_conditioning(image * 2 - 1, self.init_latent, image_mask, self.mask_round)