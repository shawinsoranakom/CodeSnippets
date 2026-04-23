def resize_annotation(
        self,
        annotation: dict[str, Any],
        orig_size: tuple[int, int],
        target_size: tuple[int, int],
        threshold: float = 0.5,
        resample: Optional["PILImageResampling | tvF.InterpolationMode | int"] = PILImageResampling.NEAREST,
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
            resample (`PILImageResampling | tvF.InterpolationMode | int`, defaults to `tvF.InterpolationMode.NEAREST_EXACT`):
                The resampling filter to use when resizing the masks.
        """
        ratio_height, ratio_width = [target / orig for target, orig in zip(target_size, orig_size)]

        new_annotation = {}
        new_annotation["size"] = target_size

        for key, value in annotation.items():
            if key == "boxes":
                boxes = value
                scaled_boxes = boxes * torch.as_tensor(
                    [ratio_width, ratio_height, ratio_width, ratio_height], dtype=torch.float32, device=boxes.device
                )
                new_annotation["boxes"] = scaled_boxes
            elif key == "area":
                area = value
                scaled_area = area * (ratio_width * ratio_height)
                new_annotation["area"] = scaled_area
            elif key == "masks":
                masks = value[:, None]
                masks = [
                    super(DeformableDetrImageProcessor, self).resize(
                        mask, size=SizeDict(height=target_size[0], width=target_size[1]), resample=resample
                    )
                    for mask in masks
                ]
                masks = torch.stack(masks).to(torch.float32)
                masks = masks[:, 0] > threshold
                new_annotation["masks"] = masks
            elif key == "size":
                new_annotation["size"] = target_size
            else:
                new_annotation[key] = value

        return new_annotation