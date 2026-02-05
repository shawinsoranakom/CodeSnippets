def gaussian_filter(image, k_size, sigma):
    height, width = image.shape[0], image.shape[1]
    dst_height = height - k_size + 1
    dst_width = width - k_size + 1

    image_array = zeros((dst_height * dst_width, k_size * k_size))
    for row, (i, j) in enumerate(product(range(dst_height), range(dst_width))):
        window = ravel(image[i : i + k_size, j : j + k_size])
        image_array[row, :] = window

    gaussian_kernel = gen_gaussian_kernel(k_size, sigma)
    filter_array = ravel(gaussian_kernel)
  
    dst = dot(image_array, filter_array).reshape(dst_height, dst_width).astype(uint8)

    return dst

