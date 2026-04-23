def detected_faces(self, faces: list[DetectedFace]) -> None:
        """Set the underlying properties from a list of DetectedFace objects

        Parameters
        ----------
        faces
            The DetectedFace objects to populate to this object

        Raises
        ------
        ValueError
            If the FrameFaces object does not contain a filename and image or if any of the data
            fields are populated
        """
        if not self.filename or not self.image.size:
            raise ValueError("Filename and image must be populated before adding DetectedFace "
                             "objects")
        if np.any(self.bboxes) or self.landmarks is not None or self.masks or self.identities:
            raise ValueError("The FrameFaces object must not be pre-populated when adding"
                             "DetectedFace objects")
        for face in faces:
            if None not in (face.left, face.top, face.width, face.height):
                bbox = np.array([[face.left, face.top, face.right, face.bottom]], dtype=np.int32)
                self.bboxes = np.concatenate([self.bboxes, bbox])
            if face.has_landmarks:
                landmarks = np.array(face.landmarks_xy, dtype=np.float32)[None]
                self.landmarks = (landmarks if self.landmarks is None
                                  else np.concatenate([self.landmarks, landmarks]))
            for k, m in face.mask.items():
                msk = ExtractBatchMask(m.stored_centering,
                                       m.affine_matrix[None],
                                       m.stored_size,
                                       m.mask[None])
                if k not in self.masks:
                    self.masks[k] = msk
                else:
                    self.masks[k].append(msk)
            for k, i in face.identity.items():
                if k not in self.identities:
                    self.identities[k] = i[None]
                else:
                    self.identities[k] = np.concatenate([self.identities[k], i[None]])