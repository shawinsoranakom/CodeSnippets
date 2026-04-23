def get_expected_values(self, image_inputs, batched=False):
        """
        This function computes the expected height and width when providing images to YolosImageProcessor,
        assuming do_resize is set to True with a scalar size.
        """
        if not batched:
            image = image_inputs[0]
            if isinstance(image, Image.Image):
                width, height = image.size
            elif isinstance(image, np.ndarray):
                height, width = image.shape[0], image.shape[1]
            else:
                height, width = image.shape[1], image.shape[2]

            size = self.size["shortest_edge"]
            max_size = self.size.get("longest_edge", None)
            if max_size is not None:
                min_original_size = float(min((height, width)))
                max_original_size = float(max((height, width)))
                if max_original_size / min_original_size * size > max_size:
                    size = int(round(max_size * min_original_size / max_original_size))

            if width <= height and width != size:
                height = int(size * height / width)
                width = size
            elif height < width and height != size:
                width = int(size * width / height)
                height = size
            width_mod = width % 16
            height_mod = height % 16
            expected_width = width - width_mod
            expected_height = height - height_mod

        else:
            expected_values = []
            for image in image_inputs:
                expected_height, expected_width = self.get_expected_values([image])
                expected_values.append((expected_height, expected_width))
            expected_height = max(expected_values, key=lambda item: item[0])[0]
            expected_width = max(expected_values, key=lambda item: item[1])[1]

        return expected_height, expected_width