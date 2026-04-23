def pan_and_scan(
        self,
        image: np.ndarray,
        pan_and_scan_min_crop_size: int,
        pan_and_scan_max_num_crops: int,
        pan_and_scan_min_ratio_to_activate: float,
    ):
        """
        Pan and Scan an image, by cropping into smaller images when the aspect ratio exceeds
        minimum allowed ratio.

        Args:
            image (`np.ndarray`):
                Image to resize.
            pan_and_scan_min_crop_size (`int`, *optional*):
                Minimum size of each crop in pan and scan.
            pan_and_scan_max_num_crops (`int`, *optional*):
                Maximum number of crops per image in pan and scan.
            pan_and_scan_min_ratio_to_activate (`float`, *optional*):
                Minimum aspect ratio to activate pan and scan.
        """
        height, width = get_image_size(image, channel_dim="channels_first")

        # Square or landscape image.
        if width >= height:
            # Only apply PaS if the image is sufficiently exaggerated
            if width / height < pan_and_scan_min_ratio_to_activate:
                return []

            # Select ideal number of crops close to the image aspect ratio and such that crop_size > min_crop_size.
            num_crops_w = int(math.floor(width / height + 0.5))  # Half round up rounding.
            num_crops_w = min(int(math.floor(width / pan_and_scan_min_crop_size)), num_crops_w)

            # Make sure the number of crops is in range [2, pan_and_scan_max_num_crops].
            num_crops_w = max(2, num_crops_w)
            num_crops_w = min(pan_and_scan_max_num_crops, num_crops_w)
            num_crops_h = 1

        # Portrait image.
        else:
            # Only apply PaS if the image is sufficiently exaggerated
            if height / width < pan_and_scan_min_ratio_to_activate:
                return []

            # Select ideal number of crops close to the image aspect ratio and such that crop_size > min_crop_size.
            num_crops_h = int(math.floor(height / width + 0.5))
            num_crops_h = min(int(math.floor(height / pan_and_scan_min_crop_size)), num_crops_h)

            # Make sure the number of crops is in range [2, pan_and_scan_max_num_crops].
            num_crops_h = max(2, num_crops_h)
            num_crops_h = min(pan_and_scan_max_num_crops, num_crops_h)
            num_crops_w = 1

        crop_size_w = int(math.ceil(width / num_crops_w))
        crop_size_h = int(math.ceil(height / num_crops_h))

        # Don't apply PaS if crop size is too small.
        if min(crop_size_w, crop_size_h) < pan_and_scan_min_crop_size:
            return []

        crop_positions_w = [crop_size_w * i for i in range(num_crops_w)]
        crop_positions_h = [crop_size_h * i for i in range(num_crops_h)]

        # Images are channels-first (CHW format)
        return [
            image[:, pos_h : pos_h + crop_size_h, pos_w : pos_w + crop_size_w]
            for pos_h, pos_w in itertools.product(crop_positions_h, crop_positions_w)
        ]