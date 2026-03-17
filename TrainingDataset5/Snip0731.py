def median_filter(gray_img, mask=3):
    bd = int(mask / 2)
    median_img = zeros_like(gray_img)
    for i in range(bd, gray_img.shape[0] - bd):
        for j in range(bd, gray_img.shape[1] - bd):
            kernel = ravel(gray_img[i - bd : i + bd + 1, j - bd : j + bd + 1])
            median = sort(kernel)[int8(divide((multiply(mask, mask)), 2) + 1)]
            median_img[i, j] = median
    return median_img
