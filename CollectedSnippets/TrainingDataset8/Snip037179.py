def __init__(self, size=200, step=10):
        self._size = size
        self._step = step
        self._half = self._size / 2
        self._data = {}

        self.create_image()
        self.generate_image_types()
        self.generate_image_channel_data()
        self.generate_bgra_image()
        self.generate_gif()
        self.generate_pseudorandom_image()
        self.generate_gray_image()
        self.save()