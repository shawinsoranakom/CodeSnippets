def canny(image, threshold_low=15, threshold_high=30, weak=128, strong=255):
    gaussian_out = img_convolve(image, gen_gaussian_kernel(9, sigma=1.4))
    sobel_grad, sobel_theta = sobel_filter(gaussian_out)
    gradient_direction = PI + np.rad2deg(sobel_theta)

    destination = suppress_non_maximum(image.shape, gradient_direction, sobel_grad)

    detect_high_low_threshold(
        image.shape, destination, threshold_low, threshold_high, weak, strong
    )

    track_edge(image.shape, destination, weak, strong)

    return destination
