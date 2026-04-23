def from_alignment(self, alignment: FileAlignments | PNGAlignments,
                       image: np.ndarray | None = None, with_thumb: bool = False) -> T.Self:
        """Set the attributes of this class from an alignments file and optionally load the face
        into the ``image`` attribute.

        Parameters
        ----------
        alignment
            The alignment object to obtain the alignments from
        image
            If an image is passed in, then the ``image`` attribute will
            be set to the cropped face based on the passed in bounding box co-ordinates
        with_thumb
            Whether to load the jpg thumbnail into the detected face object, if provided.
            Default: ``False``

        Returns
        -------
        This DetectedFace object populated by the incoming alignment dict
        """

        logger.trace("Creating from alignment: (alignment: %s,"  # type:ignore[attr-defined]
                     " has_image: %s)", alignment, bool(image is not None))
        self.left = alignment.x
        self.width = alignment.w
        self.top = alignment.y
        self.height = alignment.h
        self._identity = alignment.identity
        self._landmarks_xy = alignment.landmarks_xy
        if with_thumb and isinstance(alignment, FileAlignments):
            self.thumbnail = alignment.thumb

        # Manual tool and legacy alignments will not have a mask
        self._aligned = None

        if alignment.mask:
            self.mask = {}
            for name, mask in alignment.mask.items():
                if name in ("components", "extended"):
                    continue  # Skip legacy stored LM based masks
                self.mask[name] = aligned_mask.Mask()
                self.mask[name].from_dict(mask)
        if image is not None and image.any():
            self._image_to_face(image)
        logger.trace("Created from alignment: (left: %s, width: %s, "  # type:ignore[attr-defined]
                     "top: %s, height: %s, landmarks: %s, mask: %s)",
                     self.left, self.width, self.top, self.height, self.landmarks_xy, self.mask)
        return self