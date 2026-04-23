def map_arguments(self, augmenter_type, augmenter_args):
        augmenter_args = augmenter_args.copy()  # Avoid modifying the original arguments
        if augmenter_type == "Resize":
            # Ensure size is a valid 2-element list or tuple
            size = augmenter_args.get("size")
            if size:
                if not isinstance(size, (list, tuple)) or len(size) != 2:
                    raise ValueError(
                        f"'size' must be a list or tuple of two numbers, but got {size}"
                    )
                min_scale, max_scale = size
                return {
                    "scale_range": (min_scale, max_scale),
                    "interpolation": 1,  # Linear interpolation
                    "p": 1.0,
                }
            else:
                return {"scale_range": (1.0, 1.0), "interpolation": 1, "p": 1.0}
        elif augmenter_type == "Affine":
            # Map rotation to a tuple and ensure p=1.0 to apply transformation
            rotate = augmenter_args.get("rotate", 0)
            if isinstance(rotate, list):
                rotate = tuple(rotate)
            elif isinstance(rotate, (int, float)):
                rotate = (float(rotate), float(rotate))
            augmenter_args["rotate"] = rotate
            augmenter_args["p"] = 1.0
            return augmenter_args
        else:
            # For other augmenters, ensure 'p' probability is specified
            p = augmenter_args.get("p", 1.0)
            augmenter_args["p"] = p
            return augmenter_args