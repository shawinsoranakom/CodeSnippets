def get_expected_value(self, image_inputs):
        image = image_inputs[0]

        if isinstance(image, Image.Image):
            width, height = image.size
        elif isinstance(image, np.ndarray):
            height, width = image.shape[0], image.shape[1]
        else:
            height, width = image.shape[1], image.shape[2]

        if max(height, width) > self.limit_side_len:
            ratio = float(self.limit_side_len) / max(height, width)
        else:
            ratio = 1.0

        resize_height = int(height * ratio)
        resize_width = int(width * ratio)

        if self.max_side_limit is not None and max(resize_height, resize_width) > self.max_side_limit:
            ratio = float(self.max_side_limit) / max(resize_height, resize_width)
            resize_height = int(resize_height * ratio)
            resize_width = int(resize_width * ratio)

        resize_height = max(int(round(resize_height / 32) * 32), 32)
        resize_width = max(int(round(resize_width / 32) * 32), 32)

        if resize_height == height and resize_width == width:
            return resize_height, resize_width

        if resize_width <= 0 or resize_height <= 0:
            return None, None

        return resize_height, resize_width