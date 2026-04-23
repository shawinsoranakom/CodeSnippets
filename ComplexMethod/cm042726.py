def convert_image(
        self,
        image: Image.Image,
        size: tuple[int, int] | None = None,
        *,
        response_body: BytesIO,
    ) -> tuple[Image.Image, BytesIO]:
        if image.format in {"PNG", "WEBP"} and image.mode == "RGBA":
            background = self._Image.new("RGBA", image.size, (255, 255, 255))
            background.paste(image, image)
            image = background.convert("RGB")
        elif image.mode == "P":
            image = image.convert("RGBA")
            background = self._Image.new("RGBA", image.size, (255, 255, 255))
            background.paste(image, image)
            image = background.convert("RGB")
        elif image.mode != "RGB":
            image = image.convert("RGB")

        if size:
            image = image.copy()
            try:
                # Image.Resampling.LANCZOS was added in Pillow 9.1.0
                # remove this try except block,
                # when updating the minimum requirements for Pillow.
                resampling_filter = self._Image.Resampling.LANCZOS
            except AttributeError:
                resampling_filter = self._Image.ANTIALIAS  # type: ignore[attr-defined]
            image.thumbnail(size, resampling_filter)
        elif image.format == "JPEG":
            return image, response_body

        buf = BytesIO()
        image.save(buf, "JPEG")
        return image, buf