def copy_replace(self, sourceImage, *, from_coords=None, to=None, shrink=False,
                     zoom=None, subsample=None, compositingrule=None):
        """Copy a region from the source image (which must be a PhotoImage) to
        this image, possibly with pixel zooming and/or subsampling.  If no
        options are specified, this command copies the whole of the source
        image into this image, starting at coordinates (0, 0).

        The FROM_COORDS option specifies a rectangular sub-region of the
        source image to be copied. It must be a tuple or a list of 1 to 4
        integers (x1, y1, x2, y2).  (x1, y1) and (x2, y2) specify diagonally
        opposite corners of the rectangle.  If x2 and y2 are not specified,
        the default value is the bottom-right corner of the source image.
        The pixels copied will include the left and top edges of the
        specified rectangle but not the bottom or right edges.  If the
        FROM_COORDS option is not given, the default is the whole source
        image.

        The TO option specifies a rectangular sub-region of the destination
        image to be affected.  It must be a tuple or a list of 1 to 4
        integers (x1, y1, x2, y2).  (x1, y1) and (x2, y2) specify diagonally
        opposite corners of the rectangle.  If x2 and y2 are not specified,
        the default value is (x1,y1) plus the size of the source region
        (after subsampling and zooming, if specified).  If x2 and y2 are
        specified, the source region will be replicated if necessary to fill
        the destination region in a tiled fashion.

        If SHRINK is true, the size of the destination image should be
        reduced, if necessary, so that the region being copied into is at
        the bottom-right corner of the image.

        If SUBSAMPLE or ZOOM are specified, the image is transformed as in
        the subsample() or zoom() methods.  The value must be a single
        integer or a pair of integers.

        The COMPOSITINGRULE option specifies how transparent pixels in the
        source image are combined with the destination image.  When a
        compositing rule of 'overlay' is set, the old contents of the
        destination image are visible, as if the source image were printed
        on a piece of transparent film and placed over the top of the
        destination.  When a compositing rule of 'set' is set, the old
        contents of the destination image are discarded and the source image
        is used as-is.  The default compositing rule is 'overlay'.
        """
        options = []
        if from_coords is not None:
            options.extend(('-from', *from_coords))
        if to is not None:
            options.extend(('-to', *to))
        if shrink:
            options.append('-shrink')
        if zoom is not None:
            if not isinstance(zoom, (tuple, list)):
                zoom = (zoom,)
            options.extend(('-zoom', *zoom))
        if subsample is not None:
            if not isinstance(subsample, (tuple, list)):
                subsample = (subsample,)
            options.extend(('-subsample', *subsample))
        if compositingrule:
            options.extend(('-compositingrule', compositingrule))
        self.tk.call(self.name, 'copy', sourceImage, *options)