def _random_warp_landmarks(self,
                               batch: np.ndarray,
                               batch_src_points: np.ndarray,
                               batch_dst_points: np.ndarray) -> np.ndarray:
        """From dfaker. Warp the image to a similar set of landmarks from the opposite side

        batch
            The batch should be a 4-dimensional array of shape (`batchsize`, `height`, `width`,
            `3`) and in `BGR` format.
        batch_src_points
            A batch of 68 point landmarks for the source faces. This is a 3-dimensional array in
            the shape (`batchsize`, `68`, `2`).
        batch_dst_points
            A batch of randomly chosen closest match destination faces landmarks. This is a
            3-dimensional array in the shape (`batchsize`, `68`, `2`).

        Returns
        ----------
        A 4-dimensional array of the same shape as :attr:`batch` with warping applied.
        """
        logger.trace("[Aug] Randomly warping landmarks")  # type:ignore[attr-defined]
        edge_anchors = self._constants.warp.lm_edge_anchors
        grids = self._constants.warp.lm_grids

        batch_dst = batch_dst_points + np.random.normal(size=batch_dst_points.shape,
                                                        scale=self._constants.warp.lm_scale)

        face_cores = [cv2.convexHull(np.concatenate([src[17:], dst[17:]], axis=0))
                      for src, dst in zip(batch_src_points.astype("int32"),
                                          batch_dst.astype("int32"))]

        batch_src = np.append(batch_src_points, edge_anchors, axis=1)
        batch_dst = np.append(batch_dst, edge_anchors, axis=1)

        rem_indices = [list(set(idx for fpl in (src, dst)
                                for idx, (pty, ptx) in enumerate(fpl)
                                if cv2.pointPolygonTest(face_core, (pty, ptx), False) >= 0))
                       for src, dst, face_core in zip(batch_src[:, :18, :],
                                                      batch_dst[:, :18, :],
                                                      face_cores)]
        lm_batch_src = [np.delete(src, indices, axis=0)
                        for indices, src in zip(rem_indices, batch_src)]
        lm_batch_dst = [np.delete(dst, indices, axis=0)
                        for indices, dst in zip(rem_indices, batch_dst)]

        grid_z = np.array([griddata(dst, src, (grids[0], grids[1]), method="linear")
                           for src, dst in zip(lm_batch_src, lm_batch_dst)])
        maps = grid_z.reshape((self._batch_size,
                               self._processing_size,
                               self._processing_size,
                               2)).astype("float32")

        warped_batch = np.array([cv2.remap(image,
                                           map_[..., 1],
                                           map_[..., 0],
                                           cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_TRANSPARENT)
                                 for image, map_ in zip(batch, maps)])
        logger.trace("[Aug] Warped batch shape: %s",  # type:ignore[attr-defined]
                     warped_batch.shape)
        return warped_batch