def image(
        self,
        image: ImageOrImageList,
        # TODO: Narrow type of caption, dependent on type of image,
        #  by way of overload
        caption: Optional[Union[str, List[str]]] = None,
        width: Optional[int] = None,
        use_column_width: UseColumnWith = None,
        clamp: bool = False,
        channels: Channels = "RGB",
        output_format: ImageFormatOrAuto = "auto",
    ) -> "DeltaGenerator":
        """Display an image or list of images.

        Parameters
        ----------
        image : numpy.ndarray, [numpy.ndarray], BytesIO, str, or [str]
            Monochrome image of shape (w,h) or (w,h,1)
            OR a color image of shape (w,h,3)
            OR an RGBA image of shape (w,h,4)
            OR a URL to fetch the image from
            OR a path of a local image file
            OR an SVG XML string like `<svg xmlns=...</svg>`
            OR a list of one of the above, to display multiple images.
        caption : str or list of str
            Image caption. If displaying multiple images, caption should be a
            list of captions (one for each image).
        width : int or None
            Image width. None means use the image width,
            but do not exceed the width of the column.
            Should be set for SVG images, as they have no default image width.
        use_column_width : 'auto' or 'always' or 'never' or bool
            If 'auto', set the image's width to its natural size,
            but do not exceed the width of the column.
            If 'always' or True, set the image's width to the column width.
            If 'never' or False, set the image's width to its natural size.
            Note: if set, `use_column_width` takes precedence over the `width` parameter.
        clamp : bool
            Clamp image pixel values to a valid range ([0-255] per channel).
            This is only meaningful for byte array images; the parameter is
            ignored for image URLs. If this is not set, and an image has an
            out-of-range value, an error will be thrown.
        channels : 'RGB' or 'BGR'
            If image is an nd.array, this parameter denotes the format used to
            represent color information. Defaults to 'RGB', meaning
            `image[:, :, 0]` is the red channel, `image[:, :, 1]` is green, and
            `image[:, :, 2]` is blue. For images coming from libraries like
            OpenCV you should set this to 'BGR', instead.
        output_format : 'JPEG', 'PNG', or 'auto'
            This parameter specifies the format to use when transferring the
            image data. Photos should use the JPEG format for lossy compression
            while diagrams should use the PNG format for lossless compression.
            Defaults to 'auto' which identifies the compression type based
            on the type and format of the image argument.

        Example
        -------
        >>> from PIL import Image
        >>> image = Image.open('sunrise.jpg')
        >>>
        >>> st.image(image, caption='Sunrise by the mountains')

        .. output::
           https://doc-image.streamlitapp.com/
           height: 710px

        """

        if use_column_width == "auto" or (use_column_width is None and width is None):
            width = -3
        elif use_column_width == "always" or use_column_width == True:
            width = -2
        elif width is None:
            width = -1
        elif width <= 0:
            raise StreamlitAPIException("Image width must be positive.")

        image_list_proto = ImageListProto()
        marshall_images(
            self.dg._get_delta_path_str(),
            image,
            caption,
            width,
            image_list_proto,
            clamp,
            channels,
            output_format,
        )
        return self.dg._enqueue("imgs", image_list_proto)