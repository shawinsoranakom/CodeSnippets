def _get_segment_indices(self) -> list[int]:
        """Obtain the segment indices to include within the face mask area based on user
        configuration settings.

        Returns
        -------
        The segment indices to include within the face mask area

        Notes
        -----
        'original' Model segment indices:
        0: background, 1: skin, 2: left brow, 3: right brow, 4: left eye, 5: right eye, 6: glasses
        7: left ear, 8: right ear, 9: earing, 10: nose, 11: mouth, 12: upper lip, 13: lower_lip,
        14: neck, 15: neck ?, 16: cloth, 17: hair, 18: hat

        'faceswap' Model segment indices:
        0: background, 1: skin, 2: ears, 3: hair, 4: glasses
        """
        retval = [1] if self._is_faceswap else [1, 2, 3, 4, 5, 10, 11, 12, 13]

        if cfg.include_glasses():
            retval.append(4 if self._is_faceswap else 6)
        if cfg.include_ears():
            retval.extend([2] if self._is_faceswap else [7, 8, 9])
        if cfg.include_hair():
            retval.append(3 if self._is_faceswap else 17)
        logger.debug("Selected segment indices: %s", retval)
        return retval