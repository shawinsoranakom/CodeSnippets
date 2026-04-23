def transform_images(self, images, transformation, training=True):
        if training:
            images = self.backend.cast(images, self.compute_dtype)
            crop_box_hstart, crop_box_wstart = transformation
            crop_height = self.height
            crop_width = self.width

            if self.data_format == "channels_last":
                if len(images.shape) == 4:
                    images = images[
                        :,
                        crop_box_hstart : crop_box_hstart + crop_height,
                        crop_box_wstart : crop_box_wstart + crop_width,
                        :,
                    ]
                else:
                    images = images[
                        crop_box_hstart : crop_box_hstart + crop_height,
                        crop_box_wstart : crop_box_wstart + crop_width,
                        :,
                    ]
            else:
                if len(images.shape) == 4:
                    images = images[
                        :,
                        :,
                        crop_box_hstart : crop_box_hstart + crop_height,
                        crop_box_wstart : crop_box_wstart + crop_width,
                    ]
                else:
                    images = images[
                        :,
                        crop_box_hstart : crop_box_hstart + crop_height,
                        crop_box_wstart : crop_box_wstart + crop_width,
                    ]

            shape = self.backend.shape(images)
            new_height = shape[self.height_axis]
            new_width = shape[self.width_axis]
            if (
                not isinstance(new_height, int)
                or not isinstance(new_width, int)
                or new_height != self.height
                or new_width != self.width
            ):
                # Resize images if size mismatch or
                # if size mismatch cannot be determined
                # (in the case of a TF dynamic shape).
                images = self.backend.image.resize(
                    images,
                    size=(self.height, self.width),
                    data_format=self.data_format,
                )
                # Resize may have upcasted the outputs
                images = self.backend.cast(images, self.compute_dtype)
        return images