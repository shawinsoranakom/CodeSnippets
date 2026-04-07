def high_contrast(self):
        self.set_emulated_media(features=[{"name": "forced-colors", "value": "active"}])
        with self.desktop_size():
            try:
                yield
            finally:
                self.set_emulated_media(
                    features=[{"name": "forced-colors", "value": "none"}]
                )