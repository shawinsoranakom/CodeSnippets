def generate_gray_image(self):
        gray = (
            np.tile(np.arange(self._size) / self._size * 255, self._size)
            .reshape(self._size, self._size)
            .astype("uint8")
        )

        data = io.BytesIO()
        Image.fromarray(gray).save(data, format="PNG")
        self._data["gray.png"] = data.getvalue()