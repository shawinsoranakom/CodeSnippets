def __init__(self, input_img, threshold: int):
    self.min_threshold = 0
    self.max_threshold = int(self.get_greyscale(255, 255, 255))

    if not self.min_threshold < threshold < self.max_threshold:
        msg = f"Factor value should be from 0 to {self.max_threshold}"
        raise ValueError(msg)

    self.input_img = input_img
    self.threshold = threshold
    self.width, self.height = self.input_img.shape[1], self.input_img.shape[0]
    self.error_table = [
        [0 for _ in range(self.height + 4)] for __ in range(self.width + 1)
    ]
    self.output_img = np.ones((self.width, self.height, 3), np.uint8) * 255
