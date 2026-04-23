def convert_to_multispectral(path: str | Path, n_channels: int = 10, replace: bool = False, zip: bool = False):
    """Convert RGB images to multispectral images by interpolating across wavelength bands.

    This function takes RGB images and interpolates them to create multispectral images with a specified number of
    channels. It can process either a single image or a directory of images.

    Args:
        path (str | Path): Path to an image file or directory containing images to convert.
        n_channels (int): Number of spectral channels to generate in the output image.
        replace (bool): Whether to replace the original image file with the converted one.
        zip (bool): Whether to zip the converted images into a zip file.

    Examples:
        Convert a single image
        >>> convert_to_multispectral("path/to/image.jpg", n_channels=10)

        Convert a dataset
        >>> convert_to_multispectral("coco8", n_channels=10)
    """
    from scipy.interpolate import interp1d

    from ultralytics.data.utils import IMG_FORMATS

    path = Path(path)
    if path.is_dir():
        # Process directory
        im_files = [f for ext in (IMG_FORMATS - {"tif", "tiff"}) for f in path.rglob(f"*.{ext}")]
        for im_path in im_files:
            try:
                convert_to_multispectral(im_path, n_channels)
                if replace:
                    im_path.unlink()
            except Exception as e:
                LOGGER.info(f"Error converting {im_path}: {e}")

        if zip:
            zip_directory(path)
    else:
        # Process a single image
        output_path = path.with_suffix(".tiff")
        img = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)

        # Interpolate all pixels at once
        rgb_wavelengths = np.array([650, 510, 475])  # R, G, B wavelengths (nm)
        target_wavelengths = np.linspace(450, 700, n_channels)
        f = interp1d(rgb_wavelengths.T, img, kind="linear", bounds_error=False, fill_value="extrapolate")
        multispectral = f(target_wavelengths)
        cv2.imwritemulti(str(output_path), np.clip(multispectral, 0, 255).astype(np.uint8).transpose(2, 0, 1))
        LOGGER.info(f"Converted {output_path}")