def resize(im, w, h):
        if upscaler_name is None or upscaler_name == "None" or im.mode == 'L':
            return im.resize((w, h), resample=LANCZOS)

        scale = max(w / im.width, h / im.height)

        if scale > 1.0:
            upscalers = [x for x in shared.sd_upscalers if x.name == upscaler_name]
            if len(upscalers) == 0:
                upscaler = shared.sd_upscalers[0]
                print(f"could not find upscaler named {upscaler_name or '<empty string>'}, using {upscaler.name} as a fallback")
            else:
                upscaler = upscalers[0]

            im = upscaler.scaler.upscale(im, scale, upscaler.data_path)

        if im.width != w or im.height != h:
            im = im.resize((w, h), resample=LANCZOS)

        return im