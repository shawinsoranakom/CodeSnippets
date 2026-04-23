def execute(
        cls,
        image1,
        direction,
        match_image_size,
        spacing_width,
        spacing_color,
        image2=None,
    ) -> IO.NodeOutput:
        if image2 is None:
            return IO.NodeOutput(image1)

        # Handle batch size differences
        if image1.shape[0] != image2.shape[0]:
            max_batch = max(image1.shape[0], image2.shape[0])
            if image1.shape[0] < max_batch:
                image1 = torch.cat(
                    [image1, image1[-1:].repeat(max_batch - image1.shape[0], 1, 1, 1)]
                )
            if image2.shape[0] < max_batch:
                image2 = torch.cat(
                    [image2, image2[-1:].repeat(max_batch - image2.shape[0], 1, 1, 1)]
                )

        # Match image sizes if requested
        if match_image_size:
            h1, w1 = image1.shape[1:3]
            h2, w2 = image2.shape[1:3]
            aspect_ratio = w2 / h2

            if direction in ["left", "right"]:
                target_h, target_w = h1, int(h1 * aspect_ratio)
            else:  # up, down
                target_w, target_h = w1, int(w1 / aspect_ratio)

            image2 = comfy.utils.common_upscale(
                image2.movedim(-1, 1), target_w, target_h, "lanczos", "disabled"
            ).movedim(1, -1)

        color_map = {
            "white": 1.0,
            "black": 0.0,
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 1.0, 0.0),
            "blue": (0.0, 0.0, 1.0),
        }

        color_val = color_map[spacing_color]

        # When not matching sizes, pad to align non-concat dimensions
        if not match_image_size:
            h1, w1 = image1.shape[1:3]
            h2, w2 = image2.shape[1:3]
            pad_value = 0.0
            if not isinstance(color_val, tuple):
                pad_value = color_val

            if direction in ["left", "right"]:
                # For horizontal concat, pad heights to match
                if h1 != h2:
                    target_h = max(h1, h2)
                    if h1 < target_h:
                        pad_h = target_h - h1
                        pad_top, pad_bottom = pad_h // 2, pad_h - pad_h // 2
                        image1 = torch.nn.functional.pad(image1, (0, 0, 0, 0, pad_top, pad_bottom), mode='constant', value=pad_value)
                    if h2 < target_h:
                        pad_h = target_h - h2
                        pad_top, pad_bottom = pad_h // 2, pad_h - pad_h // 2
                        image2 = torch.nn.functional.pad(image2, (0, 0, 0, 0, pad_top, pad_bottom), mode='constant', value=pad_value)
            else:  # up, down
                # For vertical concat, pad widths to match
                if w1 != w2:
                    target_w = max(w1, w2)
                    if w1 < target_w:
                        pad_w = target_w - w1
                        pad_left, pad_right = pad_w // 2, pad_w - pad_w // 2
                        image1 = torch.nn.functional.pad(image1, (0, 0, pad_left, pad_right), mode='constant', value=pad_value)
                    if w2 < target_w:
                        pad_w = target_w - w2
                        pad_left, pad_right = pad_w // 2, pad_w - pad_w // 2
                        image2 = torch.nn.functional.pad(image2, (0, 0, pad_left, pad_right), mode='constant', value=pad_value)

        # Ensure same number of channels
        if image1.shape[-1] != image2.shape[-1]:
            max_channels = max(image1.shape[-1], image2.shape[-1])
            if image1.shape[-1] < max_channels:
                image1 = torch.cat(
                    [
                        image1,
                        torch.ones(
                            *image1.shape[:-1],
                            max_channels - image1.shape[-1],
                            device=image1.device,
                        ),
                    ],
                    dim=-1,
                )
            if image2.shape[-1] < max_channels:
                image2 = torch.cat(
                    [
                        image2,
                        torch.ones(
                            *image2.shape[:-1],
                            max_channels - image2.shape[-1],
                            device=image2.device,
                        ),
                    ],
                    dim=-1,
                )

        # Add spacing if specified
        if spacing_width > 0:
            spacing_width = spacing_width + (spacing_width % 2)  # Ensure even

            if direction in ["left", "right"]:
                spacing_shape = (
                    image1.shape[0],
                    max(image1.shape[1], image2.shape[1]),
                    spacing_width,
                    image1.shape[-1],
                )
            else:
                spacing_shape = (
                    image1.shape[0],
                    spacing_width,
                    max(image1.shape[2], image2.shape[2]),
                    image1.shape[-1],
                )

            spacing = torch.full(spacing_shape, 0.0, device=image1.device)
            if isinstance(color_val, tuple):
                for i, c in enumerate(color_val):
                    if i < spacing.shape[-1]:
                        spacing[..., i] = c
                if spacing.shape[-1] == 4:  # Add alpha
                    spacing[..., 3] = 1.0
            else:
                spacing[..., : min(3, spacing.shape[-1])] = color_val
                if spacing.shape[-1] == 4:
                    spacing[..., 3] = 1.0

        # Concatenate images
        images = [image2, image1] if direction in ["left", "up"] else [image1, image2]
        if spacing_width > 0:
            images.insert(1, spacing)

        concat_dim = 2 if direction in ["left", "right"] else 1
        return IO.NodeOutput(torch.cat(images, dim=concat_dim))