def sobel_filter(image):
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[1, 2, 1], [0, 0, 0], [-1, -2, -1]])

    dst_x = np.abs(img_convolve(image, kernel_x))
    dst_y = np.abs(img_convolve(image, kernel_y))
    dst_x = dst_x * 255 / np.max(dst_x)
    dst_y = dst_y * 255 / np.max(dst_y)

    dst_xy = np.sqrt((np.square(dst_x)) + (np.square(dst_y)))
    dst_xy = dst_xy * 255 / np.max(dst_xy)
    dst = dst_xy.astype(np.uint8)

    theta = np.arctan2(dst_y, dst_x)
    return dst, theta
