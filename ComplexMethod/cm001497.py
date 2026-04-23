def run(self, p, _, pixels, mask_blur, direction, noise_q, color_variation):
        initial_seed_and_info = [None, None]

        process_width = p.width
        process_height = p.height

        p.inpaint_full_res = False
        p.inpainting_fill = 1
        p.do_not_save_samples = True
        p.do_not_save_grid = True

        left = pixels if "left" in direction else 0
        right = pixels if "right" in direction else 0
        up = pixels if "up" in direction else 0
        down = pixels if "down" in direction else 0

        if left > 0 or right > 0:
            mask_blur_x = mask_blur
        else:
            mask_blur_x = 0

        if up > 0 or down > 0:
            mask_blur_y = mask_blur
        else:
            mask_blur_y = 0

        p.mask_blur_x = mask_blur_x*4
        p.mask_blur_y = mask_blur_y*4

        init_img = p.init_images[0]
        target_w = math.ceil((init_img.width + left + right) / 64) * 64
        target_h = math.ceil((init_img.height + up + down) / 64) * 64

        if left > 0:
            left = left * (target_w - init_img.width) // (left + right)

        if right > 0:
            right = target_w - init_img.width - left

        if up > 0:
            up = up * (target_h - init_img.height) // (up + down)

        if down > 0:
            down = target_h - init_img.height - up

        def expand(init, count, expand_pixels, is_left=False, is_right=False, is_top=False, is_bottom=False):
            is_horiz = is_left or is_right
            is_vert = is_top or is_bottom
            pixels_horiz = expand_pixels if is_horiz else 0
            pixels_vert = expand_pixels if is_vert else 0

            images_to_process = []
            output_images = []
            for n in range(count):
                res_w = init[n].width + pixels_horiz
                res_h = init[n].height + pixels_vert
                process_res_w = math.ceil(res_w / 64) * 64
                process_res_h = math.ceil(res_h / 64) * 64

                img = Image.new("RGB", (process_res_w, process_res_h))
                img.paste(init[n], (pixels_horiz if is_left else 0, pixels_vert if is_top else 0))
                mask = Image.new("RGB", (process_res_w, process_res_h), "white")
                draw = ImageDraw.Draw(mask)
                draw.rectangle((
                    expand_pixels + mask_blur_x if is_left else 0,
                    expand_pixels + mask_blur_y if is_top else 0,
                    mask.width - expand_pixels - mask_blur_x if is_right else res_w,
                    mask.height - expand_pixels - mask_blur_y if is_bottom else res_h,
                ), fill="black")

                np_image = (np.asarray(img) / 255.0).astype(np.float64)
                np_mask = (np.asarray(mask) / 255.0).astype(np.float64)
                noised = get_matched_noise(np_image, np_mask, noise_q, color_variation)
                output_images.append(Image.fromarray(np.clip(noised * 255., 0., 255.).astype(np.uint8), mode="RGB"))

                target_width = min(process_width, init[n].width + pixels_horiz) if is_horiz else img.width
                target_height = min(process_height, init[n].height + pixels_vert) if is_vert else img.height
                p.width = target_width if is_horiz else img.width
                p.height = target_height if is_vert else img.height

                crop_region = (
                    0 if is_left else output_images[n].width - target_width,
                    0 if is_top else output_images[n].height - target_height,
                    target_width if is_left else output_images[n].width,
                    target_height if is_top else output_images[n].height,
                )
                mask = mask.crop(crop_region)
                p.image_mask = mask

                image_to_process = output_images[n].crop(crop_region)
                images_to_process.append(image_to_process)

            p.init_images = images_to_process

            latent_mask = Image.new("RGB", (p.width, p.height), "white")
            draw = ImageDraw.Draw(latent_mask)
            draw.rectangle((
                expand_pixels + mask_blur_x * 2 if is_left else 0,
                expand_pixels + mask_blur_y * 2 if is_top else 0,
                mask.width - expand_pixels - mask_blur_x * 2 if is_right else res_w,
                mask.height - expand_pixels - mask_blur_y * 2 if is_bottom else res_h,
            ), fill="black")
            p.latent_mask = latent_mask

            proc = process_images(p)

            if initial_seed_and_info[0] is None:
                initial_seed_and_info[0] = proc.seed
                initial_seed_and_info[1] = proc.info

            for n in range(count):
                output_images[n].paste(proc.images[n], (0 if is_left else output_images[n].width - proc.images[n].width, 0 if is_top else output_images[n].height - proc.images[n].height))
                output_images[n] = output_images[n].crop((0, 0, res_w, res_h))

            return output_images

        batch_count = p.n_iter
        batch_size = p.batch_size
        p.n_iter = 1
        state.job_count = batch_count * ((1 if left > 0 else 0) + (1 if right > 0 else 0) + (1 if up > 0 else 0) + (1 if down > 0 else 0))
        all_processed_images = []

        for i in range(batch_count):
            imgs = [init_img] * batch_size
            state.job = f"Batch {i + 1} out of {batch_count}"

            if left > 0:
                imgs = expand(imgs, batch_size, left, is_left=True)
            if right > 0:
                imgs = expand(imgs, batch_size, right, is_right=True)
            if up > 0:
                imgs = expand(imgs, batch_size, up, is_top=True)
            if down > 0:
                imgs = expand(imgs, batch_size, down, is_bottom=True)

            all_processed_images += imgs

        all_images = all_processed_images

        combined_grid_image = images.image_grid(all_processed_images)
        unwanted_grid_because_of_img_count = len(all_processed_images) < 2 and opts.grid_only_if_multiple
        if opts.return_grid and not unwanted_grid_because_of_img_count:
            all_images = [combined_grid_image] + all_processed_images

        res = Processed(p, all_images, initial_seed_and_info[0], initial_seed_and_info[1])

        if opts.samples_save:
            for img in all_processed_images:
                images.save_image(img, p.outpath_samples, "", res.seed, p.prompt, opts.samples_format, info=res.info, p=p)

        if opts.grid_save and not unwanted_grid_because_of_img_count:
            images.save_image(combined_grid_image, p.outpath_grids, "grid", res.seed, p.prompt, opts.grid_format, info=res.info, short_filename=not opts.grid_extended_filename, grid=True, p=p)

        return res