def generate_image_types(self):
        for fmt in ("jpeg", "png"):
            i = self._image.copy()
            d = ImageDraw.Draw(i)
            d.text((self._step, self._step), fmt, fill=(0xFF, 0xFF, 0xFF, 0xFF))
            # jpegs dont have alpha channels.
            if fmt == "jpeg":
                i = i.convert("RGB")
            data = io.BytesIO()
            i.save(data, format=fmt.upper())
            self._data["image.%s" % fmt] = data.getvalue()