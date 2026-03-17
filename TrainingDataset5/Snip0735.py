def convert_to_negative(img):
    pixel_h, pixel_v = img.shape[0], img.shape[1]

    for i in range(pixel_h):
        for j in range(pixel_v):
            img[i][j] = [255, 255, 255] - img[i][j]

    return img
