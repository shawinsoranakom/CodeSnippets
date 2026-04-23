def get_random_transformation(self, data, training=True, seed=None):
        ops = self.backend
        if not training:
            return None
        if isinstance(data, dict):
            images = data["images"]
        else:
            images = data
        shape = ops.core.shape(images)
        if len(shape) == 4:
            batch_size = shape[0]
            if self.data_format == "channels_last":
                image_height = shape[1]
                image_width = shape[2]
            else:
                image_height = shape[2]
                image_width = shape[3]
        else:
            batch_size = 1
            if self.data_format == "channels_last":
                image_height = shape[0]
                image_width = shape[1]
            else:
                image_height = shape[1]
                image_width = shape[2]

        if seed is None:
            seed = self._get_seed_generator(ops._backend)
        lower = self.factor[0] * 360.0
        upper = self.factor[1] * 360.0
        angle = ops.random.uniform(
            shape=(batch_size,),
            minval=lower,
            maxval=upper,
            seed=seed,
        )
        center_x, center_y = 0.5, 0.5
        rotation_matrix = self._compute_affine_matrix(
            center_x=center_x,
            center_y=center_y,
            angle=angle,
            translate_x=ops.numpy.zeros([batch_size]),
            translate_y=ops.numpy.zeros([batch_size]),
            scale=ops.numpy.ones([batch_size]),
            shear_x=ops.numpy.zeros([batch_size]),
            shear_y=ops.numpy.zeros([batch_size]),
            height=image_height,
            width=image_width,
        )
        if len(shape) == 3:
            rotation_matrix = self.backend.numpy.squeeze(
                rotation_matrix, axis=0
            )
        return {
            "angle": angle,
            "rotation_matrix": rotation_matrix,
            "image_height": image_height,
            "image_width": image_width,
            "batch_size": batch_size,
        }