def process(self) -> None:
    for y in range(self.height):
        for x in range(self.width):
            greyscale = int(self.get_greyscale(*self.input_img[y][x]))
            if self.threshold > greyscale + self.error_table[y][x]:
                self.output_img[y][x] = (0, 0, 0)
                current_error = greyscale + self.error_table[y][x]
            else:
                self.output_img[y][x] = (255, 255, 255)
                current_error = greyscale + self.error_table[y][x] - 255
            self.error_table[y][x + 1] += int(8 / 32 * current_error)
            self.error_table[y][x + 2] += int(4 / 32 * current_error)
            self.error_table[y + 1][x] += int(8 / 32 * current_error)
            self.error_table[y + 1][x + 1] += int(4 / 32 * current_error)
            self.error_table[y + 1][x + 2] += int(2 / 32 * current_error)
            self.error_table[y + 1][x - 1] += int(4 / 32 * current_error)
            self.error_table[y + 1][x - 2] += int(2 / 32 * current_error)
