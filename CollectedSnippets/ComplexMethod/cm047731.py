def image_quality(self, quality=0, output_format=''):
        """Return the image resulting of all the image processing
        operations that have been applied previously.

        The source is returned as-is if it's an SVG, or if no operations have
        been applied, the `output_format` is the same as the original format,
        and the quality is not specified.

        :param int quality: quality setting to apply. Default to 0.

            - for JPEG: 1 is worse, 95 is best. Values above 95 should be
              avoided. Falsy values will fallback to 95, but only if the image
              was changed, otherwise the original image is returned.
            - for PNG: set falsy to prevent conversion to a WEB palette.
            - for other formats: no effect.

        :param str output_format: Can be PNG, JPEG, GIF, or ICO.
            Default to the format of the original image if a valid output format,
            otherwise BMP is converted to PNG and the rest are converted to JPEG.
        :return: the final image, or ``False`` if the original ``source`` was falsy.
        :rtype: bytes | False
        """
        if not self.image:
            return self.source

        output_image = self.image

        output_format = output_format.upper() or self.original_format
        if output_format == 'BMP':
            output_format = 'PNG'
        elif output_format not in ['PNG', 'JPEG', 'GIF', 'ICO']:
            output_format = 'JPEG'

        if not self.operationsCount and output_format == self.original_format and not quality:
            return self.source

        opt = {'output_format': output_format}

        if output_format == 'PNG':
            opt['optimize'] = True
            if quality:
                if output_image.mode != 'P':
                    # Floyd Steinberg dithering by default
                    output_image = output_image.convert('RGBA').convert('P', palette=Palette.WEB, colors=256)
        if output_format == 'JPEG':
            opt['optimize'] = True
            opt['quality'] = quality or 95
        if output_format == 'GIF':
            opt['optimize'] = True
            opt['save_all'] = True

        if output_image.mode not in ["1", "L", "P", "RGB", "RGBA"] or (output_format == 'JPEG' and output_image.mode == 'RGBA'):
            output_image = output_image.convert("RGB")

        output_bytes = image_apply_opt(output_image, **opt)
        if len(output_bytes) >= len(self.source) and self.original_format == output_format and not self.operationsCount:
            # Format has not changed and image content is unchanged but the
            # reached binary is bigger: rather use the original.
            return self.source
        return output_bytes