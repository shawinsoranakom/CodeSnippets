def _get_batches_of_transformed_samples(self, index_array):
        """Gets a batch of transformed samples.

        Args:
            index_array: Array of sample indices to include in batch.
        Returns:
            A batch of transformed samples.
        """
        batch_x = np.zeros(
            (len(index_array),) + self.image_shape, dtype=self.dtype
        )
        # build batch of image data
        # self.filepaths is dynamic, is better to call it once outside the loop
        filepaths = self.filepaths
        for i, j in enumerate(index_array):
            img = image_utils.load_img(
                filepaths[j],
                color_mode=self.color_mode,
                target_size=self.target_size,
                interpolation=self.interpolation,
                keep_aspect_ratio=self.keep_aspect_ratio,
            )
            x = image_utils.img_to_array(img, data_format=self.data_format)
            # Pillow images should be closed after `load_img`,
            # but not PIL images.
            if hasattr(img, "close"):
                img.close()
            if self.image_data_generator:
                params = self.image_data_generator.get_random_transform(x.shape)
                x = self.image_data_generator.apply_transform(x, params)
                x = self.image_data_generator.standardize(x)
            batch_x[i] = x
        # optionally save augmented images to disk for debugging purposes
        if self.save_to_dir:
            for i, j in enumerate(index_array):
                img = image_utils.array_to_img(
                    batch_x[i], self.data_format, scale=True
                )
                fname = "{prefix}_{index}_{hash}.{format}".format(
                    prefix=self.save_prefix,
                    index=j,
                    hash=np.random.randint(1e7),
                    format=self.save_format,
                )
                img.save(os.path.join(self.save_to_dir, fname))
        # build batch of labels
        if self.class_mode == "input":
            batch_y = batch_x.copy()
        elif self.class_mode in {"binary", "sparse"}:
            batch_y = np.empty(len(batch_x), dtype=self.dtype)
            for i, n_observation in enumerate(index_array):
                batch_y[i] = self.classes[n_observation]
        elif self.class_mode == "categorical":
            batch_y = np.zeros(
                (len(batch_x), len(self.class_indices)), dtype=self.dtype
            )
            for i, n_observation in enumerate(index_array):
                batch_y[i, self.classes[n_observation]] = 1.0
        elif self.class_mode == "multi_output":
            batch_y = [output[index_array] for output in self.labels]
        elif self.class_mode == "raw":
            batch_y = self.labels[index_array]
        else:
            return batch_x
        if self.sample_weight is None:
            return batch_x, batch_y
        else:
            return batch_x, batch_y, self.sample_weight[index_array]