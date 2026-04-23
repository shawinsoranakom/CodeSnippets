def resize(self, max_width=0, max_height=0, expand=False):
        """Resize the image.

        The image is not resized above the current image size, unless the expand
        parameter is True. This method is used by default to create smaller versions
        of the image.

        The current ratio is preserved. To change the ratio, see `crop_resize`.

        If `max_width` or `max_height` is falsy, it will be computed from the
        other to keep the current ratio. If both are falsy, no resize is done.

        It is currently not supported for GIF because we do not handle all the
        frames properly.

        :param int max_width: max width
        :param int max_height: max height
        :param bool expand: whether or not the image size can be increased
        :return: self to allow chaining
        :rtype: ImageProcess
        """
        if self.image and self.original_format != 'GIF' and (max_width or max_height):
            w, h = self.image.size
            asked_width = max_width or (w * max_height) // h
            asked_height = max_height or (h * max_width) // w
            if expand and (asked_width > w or asked_height > h):
                self.image = self.image.resize((asked_width, asked_height))
                self.operationsCount += 1
                return self
            if asked_width != w or asked_height != h:
                self.image.thumbnail((asked_width, asked_height), Resampling.LANCZOS)
                if self.image.width != w or self.image.height != h:
                    self.operationsCount += 1
        return self