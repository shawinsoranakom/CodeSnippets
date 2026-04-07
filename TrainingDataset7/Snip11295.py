def delete(self, save=True):
        # Clear the image dimensions cache
        if hasattr(self, "_dimensions_cache"):
            del self._dimensions_cache
        super().delete(save)