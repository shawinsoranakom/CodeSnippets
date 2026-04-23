def smart_resize(
        self,
        height: int,
        width: int,
        factor: int = 28,
        min_pixels: int = MIN_PIXELS,
        max_pixels: int = MAX_PIXELS,
    ):
        """Rescales the image so that the following conditions are met:
        1. Both dimensions (height and width) are divisible by 'factor'.
        2. The total number of pixels is within the range
            ['min_pixels', 'max_pixels'].
        3. The aspect ratio of the image is maintained as closely as possible.
        """
        if height < factor or width < factor:
            print(
                f"height:{height} or width:{width} must be larger than factor:{factor}"
            )
            if height < width:
                width = round(factor / height * width)
                height = factor
            else:
                height = round(factor / width * height)
                width = factor

        elif max(height, width) / min(height, width) > 200:
            print(
                f"absolute aspect ratio must be smaller than 200, "
                f"got {max(height, width) / min(height, width)}"
            )
            if height > width:
                height = 200 * width
            else:
                width = 200 * height

        h_bar = round(height / factor) * factor
        w_bar = round(width / factor) * factor
        if h_bar * w_bar > max_pixels:
            beta = math.sqrt((height * width) / max_pixels)
            h_bar = math.floor(height / beta / factor) * factor
            w_bar = math.floor(width / beta / factor) * factor
        elif h_bar * w_bar < min_pixels:
            beta = math.sqrt(min_pixels / (height * width))
            h_bar = math.ceil(height * beta / factor) * factor
            w_bar = math.ceil(width * beta / factor) * factor
        return h_bar, w_bar