def marshall_images(
    coordinates: str,
    image: ImageOrImageList,
    caption: Optional[Union[str, "npt.NDArray[Any]", List[str]]],
    width: int,
    proto_imgs: ImageListProto,
    clamp: bool,
    channels: Channels = "RGB",
    output_format: ImageFormatOrAuto = "auto",
) -> None:
    """Fill an ImageListProto with a list of images and their captions.

    The images will be resized and reformatted as necessary.

    Parameters
    ----------
    coordinates
        A string indentifying the images' location in the frontend.
    image
        The image or images to include in the ImageListProto.
    caption
        Image caption. If displaying multiple images, caption should be a
        list of captions (one for each image).
    width
        The desired width of the image or images. This parameter will be
        passed to the frontend, where it has some special meanings:
        -1: "OriginalWidth" (display the image at its original width)
        -2: "ColumnWidth" (display the image at the width of the column it's in)
        -3: "AutoWidth" (display the image at its original width, unless it
            would exceed the width of its column in which case clamp it to
            its column width).
    proto_imgs
        The ImageListProto to fill in.
    clamp
        Clamp image pixel values to a valid range ([0-255] per channel).
        This is only meaningful for byte array images; the parameter is
        ignored for image URLs. If this is not set, and an image has an
        out-of-range value, an error will be thrown.
    channels
        If image is an nd.array, this parameter denotes the format used to
        represent color information. Defaults to 'RGB', meaning
        `image[:, :, 0]` is the red channel, `image[:, :, 1]` is green, and
        `image[:, :, 2]` is blue. For images coming from libraries like
        OpenCV you should set this to 'BGR', instead.
    output_format
        This parameter specifies the format to use when transferring the
        image data. Photos should use the JPEG format for lossy compression
        while diagrams should use the PNG format for lossless compression.
        Defaults to 'auto' which identifies the compression type based
        on the type and format of the image argument.
    """
    channels = cast(Channels, channels.upper())

    # Turn single image and caption into one element list.
    images: Sequence[AtomicImage]
    if isinstance(image, list):
        images = image
    elif isinstance(image, np.ndarray) and len(image.shape) == 4:
        images = _4d_to_list_3d(image)
    else:
        images = [image]

    if type(caption) is list:
        captions: Sequence[Optional[str]] = caption
    else:
        if isinstance(caption, str):
            captions = [caption]
        # You can pass in a 1-D Numpy array as captions.
        elif isinstance(caption, np.ndarray) and len(caption.shape) == 1:
            captions = caption.tolist()
        # If there are no captions then make the captions list the same size
        # as the images list.
        elif caption is None:
            captions = [None] * len(images)
        else:
            captions = [str(caption)]

    assert type(captions) == list, "If image is a list then caption should be as well"
    assert len(captions) == len(images), "Cannot pair %d captions with %d images." % (
        len(captions),
        len(images),
    )

    proto_imgs.width = width
    # Each image in an image list needs to be kept track of at its own coordinates.
    for coord_suffix, (image, caption) in enumerate(zip(images, captions)):
        proto_img = proto_imgs.imgs.add()
        if caption is not None:
            proto_img.caption = str(caption)

        # We use the index of the image in the input image list to identify this image inside
        # MediaFileManager. For this, we just add the index to the image's "coordinates".
        image_id = "%s-%i" % (coordinates, coord_suffix)

        is_svg = False
        if isinstance(image, str):
            # Unpack local SVG image file to an SVG string
            if image.endswith(".svg") and not image.startswith(("http://", "https://")):
                with open(image) as textfile:
                    image = textfile.read()

            # Following regex allows svg image files to start either via a "<?xml...>" tag eventually followed by a "<svg...>" tag or directly starting with a "<svg>" tag
            if re.search(r"(^\s?(<\?xml[\s\S]*<svg\s)|^\s?<svg\s|^\s?<svg>\s)", image):
                if "xlink" in image or "xmlns" not in image:
                    proto_img.markup = f"data:image/svg+xml,{image}"
                else:
                    proto_img.url = f"data:image/svg+xml,{image}"
                is_svg = True

        if not is_svg:
            proto_img.url = image_to_url(
                image, width, clamp, channels, output_format, image_id
            )