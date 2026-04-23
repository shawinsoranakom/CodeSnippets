def img_convolve(image, filter_kernel):
    height, width = image.shape[0], image.shape[1]
    k_size = filter_kernel.shape[0]
    pad_size = k_size // 2
    image_tmp = pad(image, pad_size, mode="edge")

    image_array = im2col(image_tmp, (k_size, k_size))

    kernel_array = ravel(filter_kernel)
    dst = dot(image_array, kernel_array).reshape(height, width)
    return dst
