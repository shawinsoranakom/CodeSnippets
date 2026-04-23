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