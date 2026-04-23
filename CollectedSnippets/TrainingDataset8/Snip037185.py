def generate_pseudorandom_image(self):
        w, h = self._size, self._size
        r = np.array([255 * np.sin(x / w * 2 * np.pi) for x in range(0, w)])
        g = np.array([255 * np.cos(x / w * 2 * np.pi) for x in range(0, w)])
        b = np.array([255 * np.tan(x / w * 2 * np.pi) for x in range(0, w)])

        r = np.tile(r, h).reshape(w, h).astype("uint8")
        g = np.tile(g, h).reshape(w, h).astype("uint8")
        b = np.tile(b, h).reshape(w, h).astype("uint8")

        rgb = np.stack((r, g, b)).transpose(1, 2, 0)

        data = io.BytesIO()
        Image.fromarray(rgb).save(data, format="PNG")
        self._data["pseudorandom.png"] = data.getvalue()