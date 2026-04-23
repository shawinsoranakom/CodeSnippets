def _get_mask_types(self,
                        frame: str,
                        detected_faces: list[tuple[int, DetectedFace]]) -> list[str]:
        """Get the mask type names for the select mask type. Remove any detected faces where
        the selected mask does not exist

        Parameters
        ----------
        frame
            The frame name in the alignments file
        idx
            The index of the face for this frame in the alignments file
        detected_face
            The face index and detected_face object for output

        Returns
        -------
        List of mask type names to be processed
        """
        if self._mask_type == "bisenet-fp":
            mask_types = [f"{self._mask_type}_{area}" for area in ("face", "head")]
        else:
            mask_types = [self._mask_type]

        if self._mask_type == "custom":
            mask_types.append(f"{self._mask_type}_{self._centering}")

        final_masks = set()
        for idx in reversed(range(len(detected_faces))):
            face_idx, detected_face = detected_faces[idx]
            if detected_face.mask is None or not any(mask in detected_face.mask
                                                     for mask in mask_types):
                logger.warning("Mask type '%s' does not exist for frame '%s' index %s. Skipping",
                               self._mask_type, frame, face_idx)
                del detected_faces[idx]
                continue
            final_masks.update([m for m in detected_face.mask if m in mask_types])

        retval = list(final_masks)
        logger.trace("Handling mask types: %s", retval)  # type:ignore[attr-defined]
        return retval