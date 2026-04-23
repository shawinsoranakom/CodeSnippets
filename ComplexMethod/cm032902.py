def to_pil(self):
        if self._pil is not None:
            try:
                self._pil.load()
                return self._pil
            except Exception:
                try:
                    self._pil.close()
                except Exception:
                    pass
                self._pil = None
        res_img = None
        for blob in self._blobs:
            try:
                image = Image.open(BytesIO(blob)).convert("RGB")
            except Exception as e:
                logging.info(f"LazyImage: skip bad image blob: {e}")
                continue

            if res_img is None:
                res_img = image
                continue

            new_img = concat_img(res_img, image)
            if new_img is not res_img:
                try:
                    res_img.close()
                except Exception:
                    pass
            try:
                image.close()
            except Exception:
                pass
            res_img = new_img

        self._pil = res_img
        return self._pil