def get_random_transformation(self, data, training=True, seed=None):
        if seed is None:
            seed = self._get_seed_generator(self.backend._backend)

        if isinstance(data, dict):
            input_shape = self.backend.shape(data["images"])
        else:
            input_shape = self.backend.shape(data)

        input_height, input_width = (
            input_shape[self.height_axis],
            input_shape[self.width_axis],
        )
        if input_height is None or input_width is None:
            raise ValueError(
                "RandomCrop requires the input to have a fully defined "
                f"height and width. Received: images.shape={input_shape}"
            )

        if training and input_height > self.height and input_width > self.width:
            h_start = self.backend.cast(
                self.backend.random.uniform(
                    (),
                    0,
                    maxval=float(input_height - self.height + 1),
                    seed=seed,
                ),
                "int32",
            )
            w_start = self.backend.cast(
                self.backend.random.uniform(
                    (),
                    0,
                    maxval=float(input_width - self.width + 1),
                    seed=seed,
                ),
                "int32",
            )
        else:
            crop_height = int(float(input_width * self.height) / self.width)
            crop_height = max(min(input_height, crop_height), 1)
            crop_width = int(float(input_height * self.width) / self.height)
            crop_width = max(min(input_width, crop_width), 1)
            h_start = int(float(input_height - crop_height) / 2)
            w_start = int(float(input_width - crop_width) / 2)

        return h_start, w_start