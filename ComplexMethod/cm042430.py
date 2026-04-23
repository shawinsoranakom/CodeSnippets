def _load_image_from_path(self, image_path: str, width: int | None = None, height: int | None = None,
                            alpha_premultiply: bool = False, keep_aspect_ratio: bool = True, flip_x: bool = False) -> rl.Image:
    """Load and resize an image, storing it for later automatic unloading."""
    image = rl.load_image(image_path)

    if alpha_premultiply:
      rl.image_alpha_premultiply(image)

    # Scale up load size for sharper rendering, capped at source resolution
    if self._scale != 1.0 and width is not None and height is not None:
      width = min(int(width * self._scale), image.width)
      height = min(int(height * self._scale), image.height)

    if width is not None and height is not None:
      same_dimensions = image.width == width and image.height == height

      # Resize with aspect ratio preservation if requested
      if not same_dimensions:
        if keep_aspect_ratio:
          orig_width = image.width
          orig_height = image.height

          scale_width = width / orig_width
          scale_height = height / orig_height

          # Calculate new dimensions
          scale = min(scale_width, scale_height)
          new_width = int(orig_width * scale)
          new_height = int(orig_height * scale)

          rl.image_resize(image, new_width, new_height)
        else:
          rl.image_resize(image, width, height)
    else:
      assert keep_aspect_ratio, "Cannot resize without specifying width and height"

    if flip_x:
      rl.image_flip_horizontal(image)

    return image