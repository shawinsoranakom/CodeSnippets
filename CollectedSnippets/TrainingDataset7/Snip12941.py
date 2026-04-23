def quality(self):
        try:
            quality = float(self.params.get("q", 1))
        except ValueError:
            # Discard invalid values.
            return 1

        # Valid quality values must be between 0 and 1.
        if quality < 0 or quality > 1:
            return 1

        return round(quality, 3)