def __init__(self, source, verify_resolution=True):
        """Initialize the ``source`` image for processing.

        :param bytes source: the original image binary

            No processing will be done if the `source` is falsy or if
            the image is SVG.
        :param verify_resolution: if True, make sure the original image size is not
            excessive before starting to process it. The max allowed resolution is
            defined by `IMAGE_MAX_RESOLUTION`.
        :type verify_resolution: bool
        :rtype: ImageProcess

        :raise: ValueError if `verify_resolution` is True and the image is too large
        :raise: UserError if the image can't be identified by PIL
        """
        self.source = source or False
        self.operationsCount = 0

        if not source or source[:1] == b'<' or (source[0:4] == b'RIFF' and source[8:15] == b'WEBPVP8'):
            # don't process empty source or SVG or WEBP
            self.image = False
        else:
            try:
                self.image = Image.open(io.BytesIO(source))
            except (OSError, binascii.Error):
                raise UserError(_lt("This file could not be decoded as an image file."))

            # Original format has to be saved before fixing the orientation or
            # doing any other operations because the information will be lost on
            # the resulting image.
            self.original_format = (self.image.format or '').upper()

            self.image = image_fix_orientation(self.image)

            w, h = self.image.size
            if verify_resolution and w * h > IMAGE_MAX_RESOLUTION:
                raise UserError(_lt("Too large image (above %sMpx), reduce the image size.", str(IMAGE_MAX_RESOLUTION / 1e6)))