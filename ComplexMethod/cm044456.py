def __init__(self,  # pylint:disable=too-many-arguments,too-many-positional-arguments
                 filename: str,
                 image: npt.NDArray[np.uint8],
                 bboxes: npt.NDArray[np.int32] | None = None,
                 landmarks: npt.NDArray[np.float32] | None = None,
                 identities: dict[str, npt.NDArray[np.float32]] | None = None,
                 masks: dict[str, ExtractBatchMask] | None = None,
                 source: str | None = None,
                 is_aligned: bool = False,
                 frame_metadata: PNGSource | None = None,
                 passthrough: bool = False) -> None:
        logger.trace(parse_class_init(locals()))  # type:ignore[attr-defined]
        if is_aligned:
            assert frame_metadata is not None, "frame_metadata is required for aligned images"

        self.filename = filename
        """The original file name of the original frame"""
        self.image = image
        """The original frame or a faceswap aligned face image"""
        self.bboxes = np.empty((0, 4), dtype=np.int32) if bboxes is None else bboxes
        """The (N, Left, Top, Right, Bottom) bounding boxes of the faces in the frame"""
        self.identities = {} if identities is None else identities
        """The identity matrices for each face in the frame"""
        self.masks = {} if masks is None else masks
        """The mask objects for each face in the frame"""
        self.source = source
        """The full path to the source folder or video file or ``None`` if not provided"""
        self.frame_metadata: PNGSource | None = frame_metadata
        """The frame metadata that has been added from an aligned image. ``None`` if metadata has
        not been added"""
        self.is_aligned = is_aligned
        """``True`` if :attr:`image` is an aligned faceswap image otherwise ``False``"""
        self.passthrough = passthrough
        """``True`` if the contents of this item are meant to pass straight through the extraction
        pipeline for immediate return"""
        self.image_shape = self._get_image_shape()
        """The shape of the original frame"""

        self.aligned = ExtractBatchAligned(
            landmarks=landmarks if landmarks is None else landmarks,
            landmark_type=(None if landmarks is None
                           else LandmarkType.from_shape(T.cast(tuple[int, int],
                                                               landmarks.shape[1:]))))
        """Holds the face landmarks found for this batch any any aligned data"""
        self._name = self.__class__.__name__
        """The name of this object for logging"""