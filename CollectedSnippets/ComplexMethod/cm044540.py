def _get_background_frame(self, detected_faces: list[DetectedFace], frame_dims: tuple[int, int]
                              ) -> np.ndarray:
        """Obtain the background image when final output is in full frame format. There will only
        ever be one background, even when there are multiple faces

        The output image will depend on the requested output type and whether the input is faces
        or frames

        Parameters
        ----------
        detected_faces
            Detected face objects for the output image
        frame_dims
            The size of the original frame

        Returns
        -------
        The full frame background image for applying masks to
        """
        if self._type == "mask":
            return np.zeros(frame_dims, dtype="uint8")

        if not self._input_is_faces:  # Frame is in the detected faces object
            assert detected_faces[0].image is not None
            return np.ascontiguousarray(detected_faces[0].image)

        # Outputting to frames, but input is faces. Apply the face patches to an empty canvas
        retval = np.zeros((*frame_dims, 3), dtype="uint8")
        for detected_face in detected_faces:
            assert detected_face.image is not None
            face = AlignedFace(detected_face.landmarks_xy,
                               image=detected_face.image,
                               centering="head",
                               size=detected_face.image.shape[0],
                               is_aligned=True)
            border = cv2.BORDER_TRANSPARENT if len(detected_faces) > 1 else cv2.BORDER_CONSTANT
            assert face.face is not None
            cv2.warpAffine(face.face,
                           face.adjusted_matrix,
                           tuple(reversed(frame_dims)),
                           retval,
                           flags=cv2.WARP_INVERSE_MAP | face.interpolators[1],
                           borderMode=border)
        return retval