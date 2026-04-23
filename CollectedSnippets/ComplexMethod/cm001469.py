def post_sample(self, p, ps: scripts.PostSampleArgs, enabled, power, scale, detail_preservation, mask_inf,
                    dif_thresh, dif_contr):
        if not enabled:
            return

        if not processing_uses_inpainting(p):
            return

        nmask = getattr(p, "nmask", None)
        if nmask is None:
            return

        from modules import images
        from modules.shared import opts

        settings = SoftInpaintingSettings(power, scale, detail_preservation, mask_inf, dif_thresh, dif_contr)

        # since the original code puts holes in the existing overlay images,
        # we have to rebuild them.
        self.overlay_images = []
        for img in p.init_images:

            image = images.flatten(img, opts.img2img_background_color)

            if p.paste_to is None and p.resize_mode != 3:
                image = images.resize_image(p.resize_mode, image, p.width, p.height)

            self.overlay_images.append(image.convert('RGBA'))

        if len(p.init_images) == 1:
            self.overlay_images = self.overlay_images * p.batch_size

        if getattr(ps.samples, 'already_decoded', False):
            self.masks_for_overlay = apply_masks(settings=settings,
                                                 nmask=nmask,
                                                 overlay_images=self.overlay_images,
                                                 width=p.width,
                                                 height=p.height,
                                                 paste_to=p.paste_to)
        else:
            self.masks_for_overlay = apply_adaptive_masks(settings=settings,
                                                          nmask=nmask,
                                                          latent_orig=p.init_latent,
                                                          latent_processed=ps.samples,
                                                          overlay_images=self.overlay_images,
                                                          width=p.width,
                                                          height=p.height,
                                                          paste_to=p.paste_to)