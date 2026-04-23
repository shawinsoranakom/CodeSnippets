def __call__(self, images: np.ndarray) -> list[np.ndarray]:  # pylint:disable=too-many-locals
        """first stage - fast proposal network (p-net) to obtain face candidates

        Parameters
        ----------
        images
            The batch of images to detect faces in

        Returns
        -------
        List of face candidates from P-Net
        """
        batch_size = images.shape[0]
        rectangles: list[list[list[int | float]]] = [[] for _ in range(batch_size)]
        scores: list[list[np.ndarray]] = [[] for _ in range(batch_size)]

        pnet_input = [np.empty((batch_size, r_height, r_width, 3), dtype="float32")
                      for r_height, r_width in self._pnet_sizes]

        for scale, batch, (r_height, r_width) in zip(self._pnet_scales,
                                                     pnet_input,
                                                     self._pnet_sizes):
            for idx in range(batch_size):
                cv2.resize(images[idx], (r_width, r_height), dst=batch[idx])

            feed = torch.from_numpy(batch.transpose(0, 3, 1, 2)).to(
                self.device,
                memory_format=torch.channels_last)
            with torch.inference_mode():
                cls_prob, roi = (t.cpu().numpy() for t in self._model(feed))
            cls_prob = cls_prob[:, 1]
            out_side = max(cls_prob.shape[1:3])
            cls_prob = np.swapaxes(cls_prob, 1, 2)
            for idx in range(batch_size):
                # first index 0 = class score, 1 = one hot representation
                rect, score = self._detect_face_12net(cls_prob[idx, ...],
                                                      roi[idx, ...],
                                                      out_side,
                                                      1 / scale)
                rectangles[idx].extend(rect)
                scores[idx].extend(score)

        return [nms(np.array(rect), np.array(score), 0.7, "iou")[0]  # don't output scores
                for rect, score in zip(rectangles, scores)]