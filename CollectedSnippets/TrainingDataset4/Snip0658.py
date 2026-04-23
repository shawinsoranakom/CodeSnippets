def parse_args(args: list) -> tuple:
    filename = args[1] if args[1:] else "../image_data/lena.jpg"
    spatial_variance = float(args[2]) if args[2:] else 1.0
    intensity_variance = float(args[3]) if args[3:] else 1.0
    if args[4:]:
        kernel_size = int(args[4])
        kernel_size = kernel_size + abs(kernel_size % 2 - 1)
    else:
        kernel_size = 5
    return filename, spatial_variance, intensity_variance, kernel_size

