def _compute_resized_output_size(self, image_size, size, max_size=None):
        if len(size) == 1:  # specified size only for the smallest edge
            h, w = image_size
            short, long = (w, h) if w <= h else (h, w)
            requested_new_short = size if isinstance(size, int) else size[0]

            new_short, new_long = requested_new_short, int(
                requested_new_short * long / short
            )

            if max_size is not None:
                if max_size <= requested_new_short:
                    raise ValueError(
                        f"max_size = {max_size} must be strictly greater than the requested "
                        f"size for the smaller edge size = {size}"
                    )
                if new_long > max_size:
                    new_short, new_long = int(max_size * new_short / new_long), max_size

            new_w, new_h = (new_short, new_long) if w <= h else (new_long, new_short)
        else:  # specified both h and w
            new_w, new_h = size[1], size[0]
        return [new_h, new_w]