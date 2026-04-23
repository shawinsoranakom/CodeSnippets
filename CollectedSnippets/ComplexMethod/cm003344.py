def resize_annotation(
        self,
        annotation: dict[str, Any],
        orig_size: tuple[int, int],
        target_size: tuple[int, int],
        threshold: float = 0.5,
        resample: Optional["PILImageResampling"] = PILImageResampling.NEAREST,
    ):
        """
        Resizes an annotation to a target size.

        Args:
            annotation (`dict[str, Any]`):
                The annotation dictionary.
            orig_size (`tuple[int, int]`):
                The original size of the input image.
            target_size (`tuple[int, int]`):
                The target size of the image, as returned by the preprocessing `resize` step.
            threshold (`float`, *optional*, defaults to 0.5):
                The threshold used to binarize the segmentation masks.
            resample (`PILImageResampling`, defaults to `PILImageResampling.NEAREST`):
                The resampling filter to use when resizing the masks.
        """
        ratios = tuple(float(s) / float(s_orig) for s, s_orig in zip(target_size, orig_size))
        ratio_height, ratio_width = ratios

        new_annotation = {}
        new_annotation["size"] = target_size

        for key, value in annotation.items():
            if key == "boxes":
                boxes = value
                scaled_boxes = boxes * np.asarray(
                    [ratio_width, ratio_height, ratio_width, ratio_height], dtype=np.float32
                )
                new_annotation["boxes"] = scaled_boxes
            elif key == "area":
                area = value
                scaled_area = area * (ratio_width * ratio_height)
                new_annotation["area"] = scaled_area
            elif key == "masks":
                masks = value[:, None]
                masks = np.array([resize(mask, target_size, resample=resample) for mask in masks])
                masks = masks.astype(np.float32)
                masks = masks[:, 0] > threshold
                new_annotation["masks"] = masks
            elif key == "size":
                new_annotation["size"] = target_size
            else:
                new_annotation[key] = value

        return new_annotation