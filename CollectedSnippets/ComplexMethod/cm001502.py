def upscale(self, image, info, upscaler, upscale_mode, upscale_by, max_side_length, upscale_to_width, upscale_to_height, upscale_crop):
        if upscale_mode == 1:
            upscale_by = max(upscale_to_width/image.width, upscale_to_height/image.height)
            info["Postprocess upscale to"] = f"{upscale_to_width}x{upscale_to_height}"
        else:
            info["Postprocess upscale by"] = upscale_by
            if max_side_length != 0 and max(*image.size)*upscale_by > max_side_length:
                upscale_mode = 1
                upscale_crop = False
                upscale_to_width, upscale_to_height = limit_size_by_one_dimention(image.width*upscale_by, image.height*upscale_by, max_side_length)
                upscale_by = max(upscale_to_width/image.width, upscale_to_height/image.height)
                info["Max side length"] = max_side_length

        cache_key = (hash(np.array(image.getdata()).tobytes()), upscaler.name, upscale_mode, upscale_by,  upscale_to_width, upscale_to_height, upscale_crop)
        cached_image = upscale_cache.pop(cache_key, None)

        if cached_image is not None:
            image = cached_image
        else:
            image = upscaler.scaler.upscale(image, upscale_by, upscaler.data_path)

        upscale_cache[cache_key] = image
        if len(upscale_cache) > shared.opts.upscaling_max_images_in_cache:
            upscale_cache.pop(next(iter(upscale_cache), None), None)

        if upscale_mode == 1 and upscale_crop:
            cropped = Image.new("RGB", (upscale_to_width, upscale_to_height))
            cropped.paste(image, box=(upscale_to_width // 2 - image.width // 2, upscale_to_height // 2 - image.height // 2))
            image = cropped
            info["Postprocess crop to"] = f"{image.width}x{image.height}"

        return image