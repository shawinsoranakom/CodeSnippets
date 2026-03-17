def make_sepia(img, factor: int):
    pixel_h, pixel_v = img.shape[0], img.shape[1]

    def to_grayscale(blue, green, red):
        return 0.2126 * red + 0.587 * green + 0.114 * blue

    def normalize(value):
        return min(value, 255)

    for i in range(pixel_h):
        for j in range(pixel_v):
            greyscale = int(to_grayscale(*img[i][j]))
            img[i][j] = [
                normalize(greyscale),
                normalize(greyscale + factor),
                normalize(greyscale + 2 * factor),
            ]

    return img
