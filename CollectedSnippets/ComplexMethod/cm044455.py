def from_detected_faces(self, faces: list[DetectedFace]) -> None:
        """Populate an ExtractBatch with the contents of a DetectedFace object.

        Parameters
        ----------
        faces
            The DetectedFace objects to populate this batch

        Raises
        ------
        ValueError
            If attempting to add detected faces without pre-populating filename and image or if
            bounding boxes pre-exist or if more than one frame is held in this batch
        """
        if not self.filenames:
            raise ValueError("Filenames must be populated prior to adding detected faces")
        if not self.images:
            raise ValueError("Images must be populated prior to adding detected faces")
        if len(self.filenames) != len(self.images) != 1:
            raise ValueError("Only 1 filename and image should be the batch")
        if np.any(self.bboxes):
            raise ValueError("An empty ExtractBatch object is required to add detected faces")
        self.frame_ids = np.fromiter((0 for _ in range(len(faces))), dtype=np.int32)
        self.aligned.landmark_type = LandmarkType.from_shape(T.cast(tuple[int, int],
                                                             faces[0].landmarks_xy.shape))
        num_faces = len(faces)
        self.bboxes = np.empty((num_faces, 4), dtype=np.int32)
        self.aligned.landmarks = np.empty((num_faces, *faces[0].landmarks_xy.shape),
                                          dtype=np.float32)
        self.identities = {k: np.empty((num_faces, *v.shape), dtype=np.float32)
                           for k, v in faces[0].identity.items()}
        self.masks = {
            k: ExtractBatchMask(v.stored_centering,
                                np.empty((num_faces, 2, 3), dtype=np.float32),
                                storage_size=v.stored_size,
                                masks=np.empty((num_faces, v.stored_size, v.stored_size),
                                               dtype=np.uint8))
            for k, v in faces[0].mask.items()
            }
        for i, f in enumerate(faces):
            self.bboxes[i] = np.array([f.left, f.top, f.right, f.bottom], dtype=np.int32)
            self.aligned.landmarks[i] = f.landmarks_xy
            for k, idn in f.identity.items():
                self.identities[k][i] = idn
            for k, m in f.mask.items():
                mask = self.masks[k]
                mask.matrices[i] = m.affine_matrix
                mask.masks[i] = m.mask[:, :, 0]