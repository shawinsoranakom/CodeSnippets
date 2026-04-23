def _get_slices(self) -> list[slice] | list[list[slice]]:
        """Obtain the slices that will extract the points for the given area and landmark type

        Returns
        -------
        The slices required to extract landmark points for creating a mask
        """
        parts = LANDMARK_PARTS if self._area in ("eye", "mouth") else LANDMARK_MASK_PARTS
        if self._landmark_type not in parts:
            raise FaceswapError(
                f"Landmark based masks cannot be created for {self._landmark_type.name}")

        lm_parts = parts[self._landmark_type]
        mapped = {"mouth": ["mouth_outer"],
                  "eye": ["right_eye", "left_eye"],
                  "face": list(lm_parts),
                  "face_extended": list(lm_parts)}[self._area]

        if not all(parts in lm_parts for parts in mapped):
            raise FaceswapError(
                f"Landmark based masks cannot be created for {self._landmark_type.name}")

        if self._area in ("eye", "mouth"):
            retval: list[slice] | list[list[slice]] = [slice(*lm_parts[v][:2]) for v in mapped]
        else:
            retval = [[slice(*p) for p in T.cast(list[tuple[int, int]], lm_parts[v])]
                      for v in mapped]
        logger.trace("[LM_MASK] area: '%s', slices: %s",  # type:ignore[attr-defined]
                     self._area, retval)
        return retval