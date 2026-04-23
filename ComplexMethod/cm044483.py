def __call__(self, data: list[tuple[tuple[npt.NDArray[np.uint8], int], ...]]
                 ) -> tuple[torch.Tensor, list[torch.Tensor]]:
        """Prepare the loaded samples for feeding the model, creating targets and applying
        augmentation

        Parameters
        ----------
        data
            Batch of data tuples with the loaded stacked image and masks from each loader in the
            first position and the image file index for each item in the batch in the 2nd

        Returns
        -------
        feed
            The for the (num_inputs, batch_size, H, W, C) inputs for the model
        targets
            The for the (num_inputs, batch_size, H, W, C) targets for the model
        """
        shape = data[0][0][0].shape
        batch = np.empty((self._num_inputs, self._batch_size, *shape), dtype=np.uint8)
        indices = np.empty((self._num_inputs, self._batch_size), dtype=np.int64)
        for idx in range(self._num_inputs):
            batch[idx] = [d[0][idx] for d in data]
            indices[idx] = [d[1][idx] for d in data]

        batch = batch.reshape(-1, *shape)
        landmarks = self._get_landmarks_pairs(indices)

        if self._config.augment_color:
            batch[..., :3] = self._aug.color_adjust(batch[..., :3])

        self._aug.transform(batch, landmarks)

        if self._config.flip:
            self._aug.random_flip(batch, landmarks)
        if self._color_order == "rgb":
            batch[..., :3] = batch[..., [2, 1, 0]]

        targets = self._create_targets(batch)

        feed = batch[..., :3]
        if self._config.warp and landmarks is not None and self._landmarks is not None:
            feed = self._aug.warp(feed,
                                  to_landmarks=True,
                                  batch_src_points=landmarks[:, 0],
                                  batch_dst_points=landmarks[:, 1])
        elif self._config.warp:
            feed = self._aug.warp(feed, to_landmarks=False)

        if self._resize_inputs:
            feed = to_float32(np.array([cv2.resize(image,
                                                   (self._input_size, self._input_size),
                                                   interpolation=cv2.INTER_AREA)
                                        for image in feed]))
        else:
            feed = to_float32(feed)

        feed = feed.reshape(self._num_inputs, self._batch_size, *feed.shape[1:])
        return torch.from_numpy(feed), [torch.from_numpy(x) for x in targets]