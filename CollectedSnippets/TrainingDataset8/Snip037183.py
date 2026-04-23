def generate_bgra_image(self):
        # Split Images and rearrange
        array = np.array(self._image).transpose((2, 0, 1))

        # Recombine image to BGRA
        bgra = (
            np.stack((array[2], array[1], array[0], array[3]))
            .astype(np.uint8)
            .transpose(1, 2, 0)
        )

        data = io.BytesIO()
        Image.fromarray(bgra).save(data, format="PNG")
        self._data["bgra.png"] = data.getvalue()