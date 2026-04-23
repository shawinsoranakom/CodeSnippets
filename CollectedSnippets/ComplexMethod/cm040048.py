def transform_images(self, images, transformation, training=True):
        if training:
            if backend_utils.in_tf_graph():
                self.backend.set_backend("tensorflow")
            images = self.backend.cast(images, self.compute_dtype)
            if self.brightness_factor is not None:
                if backend_utils.in_tf_graph():
                    self.random_brightness.backend.set_backend("tensorflow")
                transformation = (
                    self.random_brightness.get_random_transformation(
                        images,
                        seed=self._get_seed_generator(self.backend._backend),
                    )
                )
                images = self.random_brightness.transform_images(
                    images, transformation
                )
            if self.contrast_factor is not None:
                if backend_utils.in_tf_graph():
                    self.random_contrast.backend.set_backend("tensorflow")
                transformation = self.random_contrast.get_random_transformation(
                    images, seed=self._get_seed_generator(self.backend._backend)
                )
                transformation["contrast_factor"] = self.backend.cast(
                    transformation["contrast_factor"], dtype=self.compute_dtype
                )
                images = self.random_contrast.transform_images(
                    images, transformation
                )
            if self.saturation_factor is not None:
                if backend_utils.in_tf_graph():
                    self.random_saturation.backend.set_backend("tensorflow")
                transformation = (
                    self.random_saturation.get_random_transformation(
                        images,
                        seed=self._get_seed_generator(self.backend._backend),
                    )
                )
                images = self.random_saturation.transform_images(
                    images, transformation
                )
            if self.hue_factor is not None:
                if backend_utils.in_tf_graph():
                    self.random_hue.backend.set_backend("tensorflow")
                transformation = self.random_hue.get_random_transformation(
                    images, seed=self._get_seed_generator(self.backend._backend)
                )
                images = self.random_hue.transform_images(
                    images, transformation
                )
            images = self.backend.cast(images, self.compute_dtype)
        return images